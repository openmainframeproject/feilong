#    Copyright 2017, 2022 IBM Corp.
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
import re
import shutil
import uuid
import six
import threading
import os

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import database
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import smtclient
from zvmsdk import utils as zvmutils
from zvmsdk import vmops
from zvmsdk import utils


_VolumeOP = None
CONF = config.CONF
LOG = log.LOG

# instance parameters:
NAME = 'name'
OS_TYPE = 'os_type'
# volume parameters:
SIZE = 'size'
TYPE = 'type'
LUN = 'lun'
# connection_info parameters:
ALIAS = 'alias'
PROTOCOL = 'protocol'
FCPS = 'fcps'
WWPNS = 'wwpns'
DEDICATE = 'dedicate'


def get_volumeop():
    global _VolumeOP
    if not _VolumeOP:
        _VolumeOP = VolumeOperatorAPI()
    return _VolumeOP


@six.add_metaclass(abc.ABCMeta)
class VolumeOperatorAPI(object):
    """Volume operation APIs oriented towards SDK driver.

    The reason to design these APIs is to facilitate the SDK driver
    issuing a volume related request without knowing details. The
    details among different distributions, different instance status,
    different volume types and so on are all hidden behind these APIs.
    The only thing the issuer need to know is what it want to do on
    which targets.

    In fact, that's an ideal case. In the real world, something like
    connection_info still depends on different complex and the issuer
    needs to know how to deal with its case. Even so, these APIs can
    still make things much easier.
    """

    _fcp_manager_obj = None

    def __init__(self):
        if not VolumeOperatorAPI._fcp_manager_obj:
            VolumeOperatorAPI._fcp_manager_obj = FCPVolumeManager()
        self._volume_manager = VolumeOperatorAPI._fcp_manager_obj

    def attach_volume_to_instance(self, connection_info):
        self._volume_manager.attach(connection_info)

    def detach_volume_from_instance(self, connection_info):
        self._volume_manager.detach(connection_info)

    def volume_refresh_bootmap(self, fcpchannel, wwpn, lun,
                               wwid='',
                               transportfiles='', guest_networks=None, fcp_template_id=None):
        return self._volume_manager.volume_refresh_bootmap(fcpchannel, wwpn,
                                            lun, wwid=wwid,
                                            transportfiles=transportfiles,
                                            guest_networks=guest_networks,
                                            fcp_template_id=fcp_template_id)

    def get_volume_connector(self, assigner_id, reserve,
                             fcp_template_id=None, sp_name=None):
        return self._volume_manager.get_volume_connector(
            assigner_id, reserve, fcp_template_id=fcp_template_id,
            sp_name=sp_name)

    def check_fcp_exist_in_db(self, fcp, raise_exec=True):
        return self._volume_manager.check_fcp_exist_in_db(fcp, raise_exec)

    def get_fcp_usage(self, fcp):
        return self._volume_manager.get_fcp_usage(fcp)

    def set_fcp_usage(self, assigner_id, fcp, reserved, connections,
                      fcp_template_id):
        return self._volume_manager.set_fcp_usage(fcp, assigner_id,
                                                  reserved, connections,
                                                  fcp_template_id)

    def create_fcp_template(self, name, description: str = '',
                            fcp_devices: str = '',
                            host_default: bool = False,
                            default_sp_list: list = [],
                            min_fcp_paths_count: int = None):
        return self._volume_manager.fcp_mgr.create_fcp_template(
            name, description, fcp_devices, host_default, default_sp_list,
            min_fcp_paths_count)

    def edit_fcp_template(self, fcp_template_id, name=None,
                          description=None, fcp_devices=None,
                          host_default=None, default_sp_list=None,
                          min_fcp_paths_count=None):
        return self._volume_manager.fcp_mgr.edit_fcp_template(
            fcp_template_id, name=name, description=description,
            fcp_devices=fcp_devices, host_default=host_default,
            default_sp_list=default_sp_list, min_fcp_paths_count=min_fcp_paths_count)

    def get_fcp_templates(self, template_id_list=None, assigner_id=None,
                          default_sp_list=None, host_default=None):
        return self._volume_manager.fcp_mgr.get_fcp_templates(
            template_id_list, assigner_id, default_sp_list, host_default)

    def get_fcp_templates_details(self, template_id_list=None, raw=False,
                                  statistics=True, sync_with_zvm=False):
        return self._volume_manager.fcp_mgr.get_fcp_templates_details(
            template_id_list, raw=raw, statistics=statistics,
            sync_with_zvm=sync_with_zvm)

    def delete_fcp_template(self, template_id):
        return self._volume_manager.fcp_mgr.delete_fcp_template(template_id)


@six.add_metaclass(abc.ABCMeta)
class VolumeConfiguratorAPI(object):
    """Volume configure APIs to implement volume config jobs on the
    target instance, like: attach, detach, and so on.

    The reason to design these APIs is to hide the details among
    different Linux distributions and releases.
    """

    def __init__(self):
        self._vmop = vmops.get_vmops()
        self._dist_manager = dist.LinuxDistManager()
        self._smtclient = smtclient.get_smtclient()

    def check_IUCV_is_ready(self, assigner_id):
        # Make sure the iucv channel is ready for communication with VM
        ready = True
        try:
            self._smtclient.execute_cmd(assigner_id, 'pwd')
        except exception.SDKSMTRequestFailed as err:
            if 'UNAUTHORIZED_ERROR' in err.format_message():
                # If unauthorized, we must raise exception
                errmsg = err.results['response'][0]
                msg = ('IUCV failed to get authorization from VM %(vm)s with '
                       'error %(err)s' % {'vm': assigner_id,
                                          'err': errmsg})
                LOG.error(msg)
                raise exception.SDKVolumeOperationError(rs=6,
                                                        userid=assigner_id,
                                                        msg=errmsg)
            else:
                # In such case, we can continue without raising exception
                ready = False
                msg = ('Failed to connect VM %(vm)s with error '
                       '%(err)s, assume it is OFF status '
                       'and continue' % {'vm': assigner_id,
                                         'err': err.results['response'][0]})
                LOG.debug(msg)
        return ready

    def _get_status_code_from_systemctl(self, assigner_id, command):
        """get the status code from systemctl status
        for example, if systemctl status output:
        Main PID: 28406 (code=exited, status=0/SUCCESS)

        this function will return the 3 behind status=
        """
        output = self._smtclient.execute_cmd_direct(assigner_id, command)
        exit_code = 0
        for line in output['response']:
            if 'Main PID' in line:
                # the status code start with = and before /FAILURE
                pattern = '(?<=status=)([0-9]+)'
                ret = re.search(pattern, line)
                exit_code = int(ret.group(1))
                break
        return exit_code

    def config_attach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point):
        LOG.info("Begin to configure volume (WWPN:%s, LUN:%s) on the "
                 "virtual machine %s with FCP devices "
                 "%s." % (target_wwpns, target_lun, assigner_id, fcp_list))
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        self.configure_volume_attach(fcp_list, assigner_id, target_wwpns,
                                     target_lun, multipath, os_version,
                                     mount_point, linuxdist)
        iucv_is_ready = self.check_IUCV_is_ready(assigner_id)
        if iucv_is_ready:
            # If VM is active rather than shutdown, then restart zvmguestconfigure
            # to run punch script(i.e. reader file) in the VM operating system
            active_cmds = linuxdist.create_active_net_interf_cmd()
            ret = self._smtclient.execute_cmd_direct(
                assigner_id, active_cmds,
                timeout=CONF.volume.punch_script_execution_timeout)
            LOG.info('attach scripts return values: %s' % ret)
            if ret['rc'] != 0:
                # if return code is 64 means timeout
                # no need to check the exist code of systemctl and return
                if ret['rc'] == 64:
                    errmsg = ('Failed to configure volume in the virtual machine '
                              '%s for volume (WWPN:%s, LUN:%s) '
                              'because exceed the timeout %s.'
                              % (assigner_id, target_wwpns, target_lun,
                                 CONF.volume.punch_script_execution_timeout))
                    LOG.error(errmsg)
                    raise exception.SDKVolumeOperationError(
                        rs=8, userid=assigner_id, msg=errmsg)
                # get exit code of zvmguestconfigure.service from VM OS,
                # the exit code reflects the result of running punch script
                get_status_cmd = 'systemctl status zvmguestconfigure.service'
                exit_code = self._get_status_code_from_systemctl(
                    assigner_id, get_status_cmd)
                # Attach script exit code explanation:
                # 1: failed because multipathd service is not active
                # 2: failed because input parameters may have problems
                # 3: failed because can not found intersection between input WWPNs and lszfcp output
                # 4: failed because no disk file found in the target VM, means no volume shown in the target VM
                if exit_code == 1:
                    errmsg = ('Failed to configure volume because the '
                              'multipathd service is not active '
                              'in the target virtual machine'
                              '(userid:%s).' % assigner_id)
                elif exit_code == 2:
                    errmsg = ('Failed to configure volume because the '
                              'configuration process terminate early with '
                              'exit code %s, refer to the /var/log/messages in '
                              'target virtual machine(userid:%s) for more '
                              'details.' % (exit_code, assigner_id))
                elif exit_code == 3:
                    errmsg = ('Failed to configure volume because can not '
                              'find valid target WWPNs for FCP devices %s, '
                              'refer to the /var/log/messages in the target '
                              'virtual machine(userid:%s) for more '
                              'details.' % (fcp_list, assigner_id))
                elif exit_code == 4:
                    errmsg = ('Failed to configure volume because the '
                              'volume(target WWPN:%s, LUN:%s) did not show up in '
                              'the target virtual machine(userid:%s), please '
                              'check Fibre Channel connectivity between '
                              'the FCP devices(%s) and target WWPN.'
                              % (target_wwpns, target_lun, assigner_id, fcp_list))
                else:
                    errmsg = ('Failed to configure volume in the target '
                              'virtual machine(userid:%s) for volume'
                              '(target WWPN:%s, LUN:%s) on FCP devices %s with '
                              'exit code: %s, refer to the /var/log/messages '
                              'in the target virtual machine for more details.'
                              % (assigner_id, target_wwpns, target_lun,
                                 fcp_list, exit_code))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=8,
                                                        userid=assigner_id,
                                                        msg=errmsg)
        LOG.info("Configuration of volume (WWPN:%s, LUN:%s) on the "
                 "target virtual machine %s with FCP devices "
                 "%s is done." % (target_wwpns, target_lun, assigner_id,
                                  fcp_list))

    def config_detach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point, connections):
        LOG.info("Begin to deconfigure volume (WWPN:%s, LUN:%s) on the "
                 "virtual machine %s with FCP devices "
                 "%s." % (target_wwpns, target_lun, assigner_id, fcp_list))
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        self.configure_volume_detach(fcp_list, assigner_id, target_wwpns,
                                     target_lun, multipath, os_version,
                                     mount_point, linuxdist, connections)
        iucv_is_ready = self.check_IUCV_is_ready(assigner_id)
        if iucv_is_ready:
            # If VM is active rather than shutdown, then restart zvmguestconfigure
            # to run punch script(i.e. reader file) in the VM operating system
            active_cmds = linuxdist.create_active_net_interf_cmd()
            ret = self._smtclient.execute_cmd_direct(
                assigner_id, active_cmds,
                timeout=CONF.volume.punch_script_execution_timeout)
            LOG.info('detach scripts return values: %s' % ret)
            if ret['rc'] != 0:
                # if return code is 64 means timeout
                # no need to check the exist code of systemctl and return
                if ret['rc'] == 64:
                    errmsg = ('detach script execution in the virtual machine '
                              '%s for volume (WWPN:%s, LUN:%s) '
                              'exceed the timeout %s.'
                              % (assigner_id, target_wwpns, target_lun,
                                 CONF.volume.punch_script_execution_timeout))
                    LOG.error(errmsg)
                    raise exception.SDKVolumeOperationError(
                        rs=9, userid=assigner_id, msg=errmsg)
                get_status_cmd = 'systemctl status zvmguestconfigure.service'
                exit_code = self._get_status_code_from_systemctl(
                    assigner_id, get_status_cmd)
                # Detach script exit code explanation:
                # 1: failed because multipathd service is not active
                # 3: failed because can not found intersection between input WWPNs and lszfcp output
                # 5: failed to flush a multipath device map
                if exit_code == 1:
                    errmsg = ('Failed to deconfigure volume because the '
                              'multipathd service is not active '
                              'in the target virtual machine'
                              '(userid:%s).' % assigner_id)
                elif exit_code == 3:
                    errmsg = ('Failed to deconfigure volume because can not '
                              'find valid target WWPNs for FCP devices %s, '
                              'refer to the /var/log/messages in the target '
                              'virtual machine(userid:%s) for more '
                              'details.' % (fcp_list, assigner_id))
                elif exit_code == 5:
                    errmsg = ('Failed to deconfigure volume because '
                              'getting error when flushing the multipath '
                              'device maps, refer to the /var/log/messages in '
                              'the target virtual machine(userid:%s) for '
                              'more details.' % assigner_id)
                else:
                    errmsg = ('Failed to deconfigure volume in the target '
                              'virtual machine(userid:%s) for volume'
                              '(target WWPN:%s, LUN:%s) on FCP devices %s with '
                              'exit code: %s, refer to the /var/log/messages '
                              'in the target virtual machine for more details.'
                              % (assigner_id, target_wwpns, target_lun,
                                 fcp_list, exit_code))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=9,
                                                        userid=assigner_id,
                                                        msg=errmsg)
        LOG.info("Deconfiguration of volume (WWPN:%s, LUN:%s) on the "
                 "target virtual machine %s with FCP devices "
                 "%s is done." % (target_wwpns, target_lun, assigner_id,
                                  fcp_list))

    def _create_file(self, assigner_id, file_name, data):
        temp_folder = self._smtclient.get_guest_temp_path(assigner_id)
        file_path = os.path.join(temp_folder, file_name)
        with open(file_path, "w") as f:
            f.write(data)
        return file_path, temp_folder

    def configure_volume_attach(self, fcp_list, assigner_id, target_wwpns,
                                target_lun, multipath, os_version,
                                mount_point, linuxdist):
        """new==True means this is first attachment"""
        # get configuration commands
        fcp_list_str = ' '.join(fcp_list)
        target_wwpns_str = ' '.join(target_wwpns)
        config_cmds = linuxdist.get_volume_attach_configuration_cmds(
            fcp_list_str, target_wwpns_str, target_lun, multipath,
            mount_point)
        LOG.debug('Got volume attachment configuation cmds for %s,'
                  'the content is:%s'
                  % (assigner_id, config_cmds))
        # write commands into script file
        config_file, config_file_path = self._create_file(assigner_id,
                                                          'atvol.sh',
                                                          config_cmds)
        LOG.debug('Creating file %s to contain volume attach '
                  'configuration file' % config_file)
        # punch file into guest
        fileClass = "X"
        try:
            self._smtclient.punch_file(assigner_id, config_file, fileClass)
        finally:
            LOG.debug('Removing the folder %s ', config_file_path)
            shutil.rmtree(config_file_path)

    def configure_volume_detach(self, fcp_list, assigner_id, target_wwpns,
                                target_lun, multipath, os_version,
                                mount_point, linuxdist, connections):
        # get configuration commands
        fcp_list_str = ' '.join(fcp_list)
        target_wwpns_str = ' '.join(target_wwpns)
        config_cmds = linuxdist.get_volume_detach_configuration_cmds(
            fcp_list_str, target_wwpns_str, target_lun, multipath,
            mount_point, connections)
        LOG.debug('Got volume detachment configuation cmds for %s,'
                  'the content is:%s'
                  % (assigner_id, config_cmds))
        # write commands into script file
        config_file, config_file_path = self._create_file(assigner_id,
                                                          'devol.sh',
                                                          config_cmds)
        LOG.debug('Creating file %s to contain volume detach '
                  'configuration file' % config_file)
        # punch file into guest
        fileClass = "X"
        try:
            self._smtclient.punch_file(assigner_id, config_file, fileClass)
        finally:
            LOG.debug('Removing the folder %s ', config_file_path)
            shutil.rmtree(config_file_path)


class FCP(object):
    def __init__(self, init_info):
        self._dev_no = None
        self._dev_status = None
        self._npiv_port = None
        self._chpid = None
        self._physical_port = None
        self._assigned_id = None
        self._owner = None
        self._parse(init_info)

    @staticmethod
    def _get_value_from_line(info_line: str):
        """Get the value behind the last colon and transfer to lower cases.
        For example, input str is 'xxxxxx: VAlval'
        return value will be: valval"""
        val = info_line.split(':')[-1].strip().lower()
        return val if val else None

    def _parse(self, init_info):
        """Initialize a FCP device object from several lines of string
           describing properties of the FCP device.
           Here is a sample:
               FCP device number: 1D1E
               Status: Free
               NPIV world wide port number: C05076DE330003C2
               Channel path ID: 27
               Physical world wide port number: C05076DE33002E41
               Owner: NONE
           The format comes from the response of xCAT, do not support
           arbitrary format.
        """
        lines_per_item = constants.FCP_INFO_LINES_PER_ITEM
        if isinstance(init_info, list) and (len(init_info) == lines_per_item):
            for line in init_info:
                if 'FCP device number' in line:
                    self._dev_no = self._get_value_from_line(line)
                elif 'Status' in line:
                    self._dev_status = self._get_value_from_line(line)
                elif 'NPIV world wide port number' in line:
                    self._npiv_port = self._get_value_from_line(line)
                elif 'Channel path ID' in line:
                    self._chpid = self._get_value_from_line(line)
                    if len(self._chpid) != 2:
                        LOG.warn("CHPID value %s of FCP device %s is "
                                 "invalid!" % (self._chpid, self._dev_no))
                elif 'Physical world wide port numbe' in line:
                    self._physical_port = self._get_value_from_line(line)
                elif 'Owner' in line:
                    self._owner = self._get_value_from_line(line)
                else:
                    LOG.info('Unknown line found in FCP information:%s', line)
        else:
            LOG.warning('When parsing FCP information, got an invalid '
                        'instance %s', init_info)

    def get_dev_no(self):
        return self._dev_no

    def get_dev_status(self):
        return self._dev_status

    def get_npiv_port(self):
        return self._npiv_port

    def set_npiv_port(self, new_npiv_port: str):
        self._npiv_port = new_npiv_port

    def set_physical_port(self, new_phy_port: str):
        self._physical_port = new_phy_port

    def get_physical_port(self):
        return self._physical_port

    def get_chpid(self):
        return self._chpid

    def get_owner(self):
        return self._owner

    def is_valid(self):
        # FIXME: add validation later
        return True

    def to_tuple(self):
        """Tranfer this object to a tuple type, format is like
           (fcp_id, wwpn_npiv, wwpn_phy, chpid, state, owner)
        for example:
           ('1a06', 'c05076de33000355', 'c05076de33002641', '27', 'active',
          'user1')
        """
        return (self.get_dev_no(), self.get_npiv_port(),
                self.get_physical_port(), self.get_chpid(),
                self.get_dev_status(), self.get_owner())


class FCPManager(object):

    def __init__(self):
        # _fcp_path_info store the FCP path mapping index by path no
        self._fcp_path_mapping = {}
        self.db = database.FCPDbOperator()
        self._smtclient = smtclient.get_smtclient()
        # Sync FCP DB
        self.sync_db()

    def sync_db(self):
        """Sync FCP DB with the FCP info queried from zVM"""
        with zvmutils.ignore_errors():
            self._sync_db_with_zvm()

    def _get_all_fcp_info(self, assigner_id, status=None):
        fcp_info = self._smtclient.get_fcp_info_by_status(assigner_id, status)

        return fcp_info

    def increase_fcp_connections(self, fcp_list, assigner_id=None):
        """Increase connections of the given FCP devices

        :param fcp_list: (list) a list of FCP devices
        :param assigner_id: (str) the userid of the virtual machine
        :return fcp_connections: (dict)
            fcp_connections example {'1a10': 1, '1b10', 0}
            the values are the connections of the FCP device
        """
        with database.get_fcp_conn():
            fcp_connections = {}
            for fcp in fcp_list:
                # increase connections by 1
                fcp_connections[fcp] = self.db.increase_connections_by_assigner(fcp, assigner_id)
            return fcp_connections

    def decrease_fcp_connections(self, fcp_list):
        """Decrease connections of FCP devices by 1

        :param fcp_list: (list) a list of FCP devices
        :return fcp_connections: (dict)
            fcp_connections example { '1a10': 1, '1b10', 0 }
            the values are the connections of the FCP device
        """
        with database.get_fcp_conn():
            fcp_connections = {}
            for fcp in fcp_list:
                try:
                    LOG.info('Decreasing the connections of FCP device {}'.format(fcp))
                    # Decrease connections of FCP device by 1
                    fcp_connections[fcp] = self.db.decrease_connections(fcp)
                except exception.SDKObjectNotExistError:
                    fcp_connections[fcp] = 0
                    pass
            return fcp_connections

    def _valid_fcp_devcie_wwpn(self, fcp_list, assigner_id):
        """This method is to
        check if the FCP wwpn_npiv or wwpn_phy is empty string,
        if yes, raise error"""
        for fcp in fcp_list:
            fcp_id, wwpn_npiv, wwpn_phy, *_ = fcp
            if not wwpn_npiv:
                # wwpn_npiv not found in FCP DB
                errmsg = ("NPIV WWPN of FCP device %s not found in "
                          "database." % fcp_id)
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)
            # We use initiator to build up zones on fabric, for NPIV, the
            # virtual ports are not yet logged in when we creating zones.
            # so we will generate the physical virtual initiator mapping
            # to determine the proper zoning on the fabric.
            # Refer to #7039 for details about avoid creating zones on
            # the fabric to which there is no fcp connected.
            if not wwpn_phy:
                errmsg = ("Physical WWPN of FCP device %s not found in "
                          "database." % fcp[0])
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)

    def reserve_fcp_devices(self, fcp_list, assigner_id, fcp_template_id):
        """
        Reserve FCP devices in the FCP database and set fcp multipath template id.
        """
        self.db.reserve_fcps(fcp_list, assigner_id, fcp_template_id)

    def unreserve_fcp_devices(self, fcp_list):
        """
        Unreserve FCP devices in the FCP database and unset fcp multipath template id.
        """
        self.db.unreserve_fcps(fcp_list)

    def allocate_fcp_devices(self, assigner_id, fcp_template_id, sp_name):
        """
        Allocate and reserve FCP devices by assigner_id and fcp_template_id. In this method:
        1. If fcp_template_id is specified, then use it. If not, get the sp
           default FCP Multipath Template, if no sp default template, use host default
           FCP Multipath Template.
           If host default template is not found, then raise error.
        2. Get FCP list from db by assigner and fcp_template whose reserve=1
        3. If fcp_list is not empty, just to use them.
        4. If fcp_list is empty, get one from each path,
           then update 'reserved' and 'tmpl_id' in fcp table.

        Returns: fcp_list and fcp_template_id.
                 The fcp list data structure: [(fcp_id, wwpn_npiv, wwpn_phy)].
                 An example of fcp_list:
                 [('1c10', 'c12345abcdefg1', 'c1234abcd33002641'),
                 ('1d10', 'c12345abcdefg2', 'c1234abcd33002641')]
        """
        with database.get_fcp_conn():
            fcp_tmpl_id = fcp_template_id
            if not fcp_tmpl_id:
                LOG.info("FCP Multipath Template id is not specified when reserving FCP "
                         "devices for assigner %s." % assigner_id)
                if sp_name:
                    LOG.info("Get the default FCP Multipath Template id for Storage "
                             "Provider %s " % sp_name)
                    default_tmpl = self.db.get_sp_default_fcp_template([sp_name])
                if not sp_name or not default_tmpl:
                    LOG.info("Can not find the default FCP Multipath Template id for "
                             "storage provider %s. Get the host default FCP "
                             "template id for assigner %s" % (sp_name,
                                                              assigner_id))
                    default_tmpl = self.db.get_host_default_fcp_template()
                if default_tmpl:
                    fcp_tmpl_id = default_tmpl[0][0]
                    LOG.info("The default FCP Multipath Template id is %s." % fcp_tmpl_id)
                else:
                    errmsg = ("No FCP Multipath Template is specified and "
                              "no default FCP Multipath Template is found.")
                    LOG.error(errmsg)
                    raise exception.SDKVolumeOperationError(rs=11,
                                                            userid=assigner_id,
                                                            msg=errmsg)

            try:
                # go here, means try to attach volumes
                # first check whether this userid already has a FCP device
                # get the FCP devices belongs to assigner_id
                fcp_list = self.db.get_allocated_fcps_from_assigner(
                    assigner_id, fcp_tmpl_id)
                LOG.info("Previously allocated records %s for "
                         "instance %s in FCP Multipath Template %s." %
                         ([f['fcp_id'] for f in fcp_list],
                          assigner_id, fcp_tmpl_id))
                if not fcp_list:
                    # Sync DB to update FCP state,
                    # so that allocating new FCPs is based on the latest FCP state
                    self._sync_db_with_zvm()
                    # allocate new ones if fcp_list is empty
                    LOG.info("There is no allocated FCP devices for virtual machine %s, "
                             "allocating new ones." % assigner_id)
                    if CONF.volume.get_fcp_pair_with_same_index:
                        '''
                        If use get_fcp_pair_with_same_index,
                        then fcp pair is randomly selected from below combinations.
                        [fa00,fb00],[fa01,fb01],[fa02,fb02]
                        '''
                        free_unreserved = self.db.get_fcp_devices_with_same_index(
                            fcp_tmpl_id)
                    else:
                        '''
                        If use get_fcp_pair,
                        then fcp pair is randomly selected from below combinations.
                        [fa00,fb00],[fa01,fb00],[fa02,fb00]
                        [fa00,fb01],[fa01,fb01],[fa02,fb01]
                        [fa00,fb02],[fa01,fb02],[fa02,fb02]
                        '''
                        free_unreserved = self.db.get_fcp_devices(fcp_tmpl_id)
                    if not free_unreserved:
                        return [], fcp_tmpl_id
                    available_list = free_unreserved
                    fcp_ids = [fcp[0] for fcp in free_unreserved]
                    # record the assigner id in the fcp DB so that
                    # when the vm provision with both root and data volumes
                    # the root and data volume would get the same FCP devices
                    # with the get_volume_connector call.
                    assigner_id = assigner_id.upper()
                    self.db.reserve_fcps(fcp_ids, assigner_id, fcp_tmpl_id)
                    LOG.info("Newly allocated %s fcp for %s assigner "
                             "and FCP Multipath Template %s" %
                             (fcp_ids, assigner_id, fcp_tmpl_id))
                else:
                    # reuse the old ones if fcp_list is not empty
                    LOG.info("Found allocated fcps %s for %s in FCP Multipath Template %s, "
                             "will reuse them."
                             % ([f['fcp_id'] for f in fcp_list],
                                assigner_id, fcp_tmpl_id))
                    path_count = self.db.get_path_count(fcp_tmpl_id)
                    if len(fcp_list) != path_count:
                        LOG.warning("FCPs previously assigned to %s includes %s, "
                                    "it is not equal to the path count: %s." %
                                    (assigner_id, fcp_list, path_count))
                    self._valid_fcp_devcie_wwpn(fcp_list, assigner_id)
                    # we got it from db, let's reuse it
                    available_list = fcp_list
                return available_list, fcp_tmpl_id
            except Exception as err:
                errmsg = ("Failed to reserve FCP devices "
                          "for assigner %s by FCP Multipath Template %s error: %s"
                          % (assigner_id, fcp_template_id, err.message))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)

    def release_fcp_devices(self, assigner_id, fcp_template_id):
        """
        Release FCP devices that belongs to the assigner_id and fcp_template_id.
        In this method:
        1. Get FCP list from db by assigner and
           fcp_template whose reserved=1
        2. If fcp_list is not empty,
           choose the ones with connections=0,
           and then set reserved=0 in fcp table in db
        3. If fcp_list is empty, return empty list

        Returns: The fcp list data structure:
           [(fcp_id, wwpn_npiv, wwpn_phy, connections)].
            An example of fcp_list:
            [('1c10', 'c12345abcdefg1', 'c1234abcd33002641', 1),
             ('1d10', 'c12345abcdefg2', 'c1234abcd33002641', 0)]
            If no fcp can be gotten from db, return empty list.
        """
        with database.get_fcp_conn():
            try:
                if fcp_template_id is None:
                    errmsg = ("fcp_template_id is not specified "
                              "while releasing FCP devices.")
                    LOG.error(errmsg)
                    raise exception.SDKVolumeOperationError(rs=11,
                                                            userid=assigner_id,
                                                            msg=errmsg)
                fcp_list = self.db.get_reserved_fcps_from_assigner(
                    assigner_id, fcp_template_id)
                if fcp_list:
                    self._valid_fcp_devcie_wwpn(fcp_list, assigner_id)
                    # the data structure of fcp_list is
                    # [(fcp_id, wwpn_npiv, wwpn_phy, connections)]
                    # only unreserve the fcp with connections=0
                    fcp_ids = [fcp['fcp_id'] for fcp in fcp_list
                               if fcp['connections'] == 0]
                    if fcp_ids:
                        self.db.unreserve_fcps(fcp_ids)
                        LOG.info("Unreserve fcp device %s from "
                                 "instance %s and FCP Multipath Template %s."
                                 % (fcp_ids, assigner_id, fcp_template_id))
                    return fcp_list
                return []
            except Exception as err:
                errmsg = ("Failed to unreserve FCP devices for "
                          "assigner %s by FCP Multipath Template %s. Error: %s"
                          % (assigner_id, fcp_template_id, err.message))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)

    def get_all_fcp_pool(self, assigner_id):
        """Return a dict of all FCPs in ZVM

        fcp_dict_in_zvm example (key=FCP):
        {
            '1a06': <zvmsdk.volumeop.FCP object at 0x3ff94f74128>,
            '1a07': <zvmsdk.volumeop.FCP object at 0x3ff94f74160>,
            '1b06': <zvmsdk.volumeop.FCP object at 0x3ff94f74588>,
            '1b07': <zvmsdk.volumeop.FCP object at 0x3ff94f74710>
        }
        """
        all_fcp_info = self._get_all_fcp_info(assigner_id)
        lines_per_item = constants.FCP_INFO_LINES_PER_ITEM
        all_fcp_pool = {}
        num_fcps = len(all_fcp_info) // lines_per_item
        for n in range(0, num_fcps):
            start_line = lines_per_item * n
            end_line = lines_per_item * (n + 1)
            fcp_init_info = all_fcp_info[start_line:end_line]
            fcp = FCP(fcp_init_info)
            dev_no = fcp.get_dev_no()
            all_fcp_pool[dev_no] = fcp
        return all_fcp_pool

    def get_fcp_dict_in_db(self):
        """Return a dict of all FCPs in FCP_DB

        Note: the key of the returned dict is in lowercase.
        example (key=FCP)
        {
            'fcp_id': (fcp_id, userid, connections, reserved, wwpn_npiv,
                       wwpn_phy, chpid, state, owner, tmpl_id),
            '1a06':   ('1a06', 'C2WDL003', 2, 1, 'c05076ddf7000002',
                       'c05076ddf7001d81', 27, 'active', 'C2WDL003', ''),
            '1b08':   ('1b08', 'C2WDL003', 2, 1, 'c05076ddf7000002',
                     'c05076ddf7001d81', 27, 'active', 'C2WDL003', ''),
            '1c08':   ('1c08', 'C2WDL003', 2, 1, 'c05076ddf7000002',
                     'c05076ddf7001d81', 27, 'active', 'C2WDL003', ''),
        }
        """

        try:
            # Get all FCPs found in DB.
            fcp_in_db = self.db.get_all_fcps_of_assigner()
        except exception.SDKObjectNotExistError:
            fcp_in_db = list()
            # this method is called by _sync_db_with_zvm,
            # change this msg to warning
            # level since no record in db is normal during sync
            # such as when there is no fcp_list configured
            msg = ("No fcp records found in database and ignore "
                   "the exception.")
            LOG.warning(msg)

        fcp_dict_in_db = {fcp[0].lower(): fcp for fcp in fcp_in_db}
        return fcp_dict_in_db

    def get_fcp_dict_in_zvm(self):
        """Return a dict of all FCPs in ZVM

        Note: the key of the returned dict is in lowercase.
        fcp_dict_in_zvm example (key=FCP):
        {
            '1a06': <zvmsdk.volumeop.FCP object at 0x3ff94f74128>,
            '1a07': <zvmsdk.volumeop.FCP object at 0x3ff94f74160>,
            '1b06': <zvmsdk.volumeop.FCP object at 0x3ff94f74588>,
            '1b07': <zvmsdk.volumeop.FCP object at 0x3ff94f74710>
        }
        """
        # Get the userid of smt server
        smt_userid = zvmutils.get_smt_userid()
        # Return a dict of all FCPs in ZVM
        fcp_dict_in_zvm = self.get_all_fcp_pool(smt_userid)
        fcp_id_to_object = {fcp.lower(): fcp_dict_in_zvm[fcp]
                            for fcp in fcp_dict_in_zvm}
        return fcp_id_to_object

    def sync_fcp_table_with_zvm(self, fcp_dict_in_zvm):
        """Update FCP records queried from zVM into FCP table."""
        with database.get_fcp_conn():
            # Get a dict of all FCPs already existed in FCP table
            fcp_dict_in_db = self.get_fcp_dict_in_db()
            # Divide FCPs into three sets
            inter_set = set(fcp_dict_in_zvm) & set(fcp_dict_in_db)
            del_fcp_set = set(fcp_dict_in_db) - inter_set
            add_fcp_set = set(fcp_dict_in_zvm) - inter_set

            # Add new records into FCP table
            fcp_info_need_insert = [fcp_dict_in_zvm[fcp].to_tuple()
                                    for fcp in add_fcp_set]
            LOG.info("New FCP devices found on z/VM: {}".format(add_fcp_set))
            self.db.bulk_insert_zvm_fcp_info_into_fcp_table(
                fcp_info_need_insert)

            # Delete FCP records from FCP table
            # if it is connections=0 and reserve=0
            LOG.info("FCP devices exist in FCP table but not in "
                     "z/VM any more: {}".format(del_fcp_set))
            fcp_ids_secure_to_delete = set()
            fcp_ids_not_found = set()
            for fcp in del_fcp_set:
                # example of a FCP record in fcp_dict_in_db
                # (fcp_id, userid, connections, reserved, wwpn_npiv,
                #  wwpn_phy, chpid, state, owner, tmpl_id)
                (fcp_id, userid, connections, reserved, wwpn_npiv_db,
                 wwpn_phy_db, chpid_db, fcp_state_db,
                 fcp_owner_db, tmpl_id) = fcp_dict_in_db[fcp]
                if connections == 0 and reserved == 0:
                    fcp_ids_secure_to_delete.add(fcp)
                else:
                    # these records not found in z/VM
                    # but still in-use in FCP table
                    fcp_ids_not_found.add(fcp)
            self.db.bulk_delete_from_fcp_table(
                fcp_ids_secure_to_delete)
            LOG.info("FCP devices removed from FCP table: {}".format(
                fcp_ids_secure_to_delete))
            # For records not found in ZVM, but still in-use in DB
            # mark them as not found
            if fcp_ids_not_found:
                self.db.bulk_update_state_in_fcp_table(fcp_ids_not_found,
                                                       'notfound')
                LOG.info("Ignore the request of deleting in-use "
                         "FCPs: {}.".format(fcp_ids_not_found))

            # Update status for FCP records already existed in DB
            LOG.info("FCP devices exist in both FCP table and "
                     "z/VM: {}".format(inter_set))
            fcp_ids_need_update = set()
            for fcp in inter_set:
                # example of a FCP record in fcp_dict_in_db
                # (fcp_id, userid, connections, reserved, wwpn_npiv,
                #  wwpn_phy, chpid, state, owner, tmpl_id)
                (fcp_id, userid, connections, reserved, wwpn_npiv_db,
                 wwpn_phy_db, chpid_db, fcp_state_db,
                 fcp_owner_db, tmpl_id) = fcp_dict_in_db[fcp]
                # Get physical WWPN and NPIV WWPN queried from z/VM
                wwpn_phy_zvm = fcp_dict_in_zvm[fcp].get_physical_port()
                wwpn_npiv_zvm = fcp_dict_in_zvm[fcp].get_npiv_port()
                # Get CHPID queried from z/VM
                chpid_zvm = fcp_dict_in_zvm[fcp].get_chpid()
                # Get FCP device state queried from z/VM
                # Possible state returned by ZVM:
                # 'active', 'free' or 'offline'
                fcp_state_zvm = fcp_dict_in_zvm[fcp].get_dev_status()
                # Get owner of FCP device queried from z/VM
                # Possible FCP owner returned by ZVM:
                # VM userid: if the FCP is attached to a VM
                # A String "NONE": if the FCP is not attached
                fcp_owner_zvm = fcp_dict_in_zvm[fcp].get_owner()
                # Check WWPNs need update or not
                if wwpn_npiv_db == '' or (connections == 0 and reserved == 0):
                    # The WWPNs are secure to be updated when:
                    # case1(wwpn_npiv_db == ''): the wwpn_npiv_db is empty, for example, upgraded from 114.
                    # case2(connections == 0 and reserved == 0): the FCP device is not in use.
                    if wwpn_npiv_db != wwpn_npiv_zvm or wwpn_phy_db != wwpn_phy_zvm:
                        # only need to update wwpns when they are different
                        fcp_ids_need_update.add(fcp)
                else:
                    # For an in-used FCP device, even its WWPNs(wwpn_npiv_zvm, wwpn_phy_zvm) are changed in z/VM,
                    # we can NOT update the wwpn_npiv, wwpn_phy columns in FCP DB because the host mapping from
                    # storage provider backend is still using the old WWPNs recorded in FCP DB.
                    # To detach the volume and delete the host mapping successfully, we need make sure the WWPNs records
                    # in FCP DB unchanged in this case.
                    # Because we will copy all properties in fcp_dict_in_zvm[fcp] to DB when update a FCP property
                    # (for example, state, owner, etc),
                    # we overwrite the (wwpn_npiv_zvm, wwpn_phy_zvm) in fcp_dict_in_zvm[fcp]
                    # to old (wwpn_npiv_db, wwpn_phy_db), so that their values will not be changed when update other
                    # properties.
                    fcp_dict_in_zvm[fcp].set_npiv_port(wwpn_npiv_db)
                    fcp_dict_in_zvm[fcp].set_physical_port(wwpn_phy_db)
                # Other cases need to update FCP record in DB
                if chpid_db != chpid_zvm:
                    # Check chpid changed or not
                    fcp_ids_need_update.add(fcp)
                elif fcp_state_db != fcp_state_zvm:
                    # Check state changed or not
                    fcp_ids_need_update.add(fcp)
                elif fcp_owner_db != fcp_owner_zvm:
                    # Check owner changed or not
                    fcp_ids_need_update.add(fcp)
                else:
                    LOG.debug("No need to update record of FCP "
                              "device {}".format(fcp))
            fcp_info_need_update = [fcp_dict_in_zvm[fcp].to_tuple()
                                    for fcp in fcp_ids_need_update]
            self.db.bulk_update_zvm_fcp_info_in_fcp_table(fcp_info_need_update)
            LOG.info("FCP devices need to update records in "
                     "fcp table: {}".format(fcp_info_need_update))

    def _sync_db_with_zvm(self):
        """Sync FCP DB with the FCP info queried from zVM"""

        LOG.info("Enter: Sync FCP DB with FCP info queried from z/VM.")
        LOG.info("Querying FCP status on z/VM.")
        # Get a dict of all FCPs in ZVM
        fcp_dict_in_zvm = self.get_fcp_dict_in_zvm()
        # Update the dict of all FCPs into FCP table in database
        self.sync_fcp_table_with_zvm(fcp_dict_in_zvm)
        LOG.info("Exit: Sync FCP DB with FCP info queried from z/VM.")

    def create_fcp_template(self, name, description: str = '',
                            fcp_devices: str = '',
                            host_default: bool = False,
                            default_sp_list: list = None,
                            min_fcp_paths_count: int = None):
        """Create a FCP Multipath Template and return the basic information of
        the created template, for example:
        {
            'fcp_template': {
            'name': 'bjcb-test-template',
            'id': '36439338-db14-11ec-bb41-0201018b1dd2',
            'description': 'This is Default template',
            'host_default': True,
            'storage_providers': ['sp4', 'v7k60'],
            'min_fcp_paths_count': 2
            }
        }
        """
        LOG.info("Try to create a"
                 " FCP Multipath Template with name:%s,"
                 "description:%s, fcp devices: %s, host_default: %s,"
                 "storage_providers: %s, min_fcp_paths_count: %s."
                 % (name, description, fcp_devices, host_default,
                    default_sp_list, min_fcp_paths_count))
        # Generate a template id for this new template
        tmpl_id = str(uuid.uuid1())
        # Get fcp devices info index by path
        fcp_devices_by_path = utils.expand_fcp_list(fcp_devices)
        # If min_fcp_paths_count is not None,need validate the value
        if min_fcp_paths_count and min_fcp_paths_count > len(fcp_devices_by_path):
            msg = ("min_fcp_paths_count %s is larger than fcp device path count %s, "
                   "adjust fcp_devices or min_fcp_paths_count."
                   % (min_fcp_paths_count, len(fcp_devices_by_path)))
            LOG.error(msg)
            raise exception.SDKConflictError(modID='volume', rs=23, msg=msg)
        # Insert related records in FCP database
        self.db.create_fcp_template(tmpl_id, name, description,
                                    fcp_devices_by_path, host_default,
                                    default_sp_list, min_fcp_paths_count)
        min_fcp_paths_count_db = self.db.get_min_fcp_paths_count(tmpl_id)
        # Return template basic info
        LOG.info("A FCP Multipath Template was created with ID %s." % tmpl_id)
        return {'fcp_template': {'name': name,
                'id': tmpl_id,
                'description': description,
                'host_default': host_default,
                'storage_providers': default_sp_list if default_sp_list else [],
                'min_fcp_paths_count': min_fcp_paths_count_db}}

    def edit_fcp_template(self, fcp_template_id, name=None,
                          description=None, fcp_devices=None,
                          host_default=None, default_sp_list=None,
                          min_fcp_paths_count=None):
        """ Edit a FCP Multipath Template

        The kwargs values are pre-validated in two places:
          validate kwargs types
            in zvmsdk/sdkwsgi/schemas/volume.py
          set a kwarg as None if not passed by user
            in zvmsdk/sdkwsgi/handlers/volume.py

        If any kwarg is None, the kwarg will not be updated.

        :param fcp_template_id: template id
        :param name:            template name
        :param description:     template desc
        :param fcp_devices:     FCP devices divided into
                                different paths by semicolon
          Format:
            "fcp-devices-from-path0;fcp-devices-from-path1;..."
          Example:
            "0011-0013;0015;0017-0018",
        :param host_default: (bool)
        :param default_sp_list: (list)
          Example:
            ["SP1", "SP2"]
        :param min_fcp_paths_count  the min fcp paths count, if it is None,
                                    will not update this field in db.
        :return:
          Example
            {
              'fcp_template': {
                'name': 'bjcb-test-template',
                'id': '36439338-db14-11ec-bb41-0201018b1dd2',
                'description': 'This is Default template',
                'host_default': True,
                'storage_providers': ['sp4', 'v7k60'],
                'min_fcp_paths_count': 2
              }
            }
        """
        LOG.info("Enter: edit_fcp_template with args {}".format(
            (fcp_template_id, name, description, fcp_devices,
             host_default, default_sp_list, min_fcp_paths_count)))
        # DML in FCP database
        result = self.db.edit_fcp_template(fcp_template_id, name=name,
                                           description=description,
                                           fcp_devices=fcp_devices,
                                           host_default=host_default,
                                           default_sp_list=default_sp_list,
                                           min_fcp_paths_count=min_fcp_paths_count)
        LOG.info("Exit: edit_fcp_template")
        return result

    def _update_template_fcp_raw_usage(self, raw_usage, raw_item):
        """group raw_item with template_id and path
        raw_item format:
        [(fcp_id|tmpl_id|path|assigner_id|connections|reserved|
        wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id)]
        return format:
        {
          template_id: {
            path: [(fcp_id, template_id, assigner_id,
                     connections,
                     reserved, wwpn_npiv, wwpn_phy,
                     chpid, state, owner,
                     tmpl_id),()]
          }
        }
        """
        (fcp_id, template_id, path_id, assigner_id, connections,
         reserved, wwpn_npiv, wwpn_phy, chpid, state, owner,
         tmpl_id) = raw_item
        if not raw_usage.get(template_id, None):
            raw_usage[template_id] = {}
        if not raw_usage[template_id].get(path_id, None):
            raw_usage[template_id][path_id] = []
        # remove path_id from raw data, keep the last templ_id to
        # represent from which template this FCP has been allocated out.
        return_raw = (fcp_id, template_id, assigner_id, connections,
                      reserved, wwpn_npiv, wwpn_phy, chpid, state,
                      owner, tmpl_id)
        raw_usage[template_id][path_id].append(return_raw)
        return raw_usage

    def extract_template_info_from_raw_data(self, raw_data):
        """
        raw_data format:
        [(id|name|description|is_default|sp_name)]

        return format:
        {
            temlate_id: {
                "id": id,
                "name": name,
                "description": description,
                "host_default": is_default,
                "storage_providers": [sp_name]
            }
        }
        """
        template_dict = {}
        for item in raw_data:
            id, name, description, is_default, min_fcp_paths_count, sp_name = item
            if min_fcp_paths_count < 0:
                min_fcp_paths_count = self.db.get_path_count(id)
            if not template_dict.get(id, None):
                template_dict[id] = {"id": id,
                                     "name": name,
                                     "description": description,
                                     "host_default": bool(is_default),
                                     "storage_providers": [],
                                     "min_fcp_paths_count": min_fcp_paths_count}
            # one FCP Multipath Template can be multiple sp's default template
            if sp_name and sp_name not in template_dict[id]["storage_providers"]:
                template_dict[id]["storage_providers"].append(sp_name)
        return template_dict

    def _update_template_fcp_statistics_usage(self, statistics_usage,
                                              raw_item):
        """Transform raw usage in FCP database into statistic data.

        :param statistics_usage: (dict) to store statistics info
        :param raw_item: [list] to represent db query result

        raw_item format:

        (fcp_id|tmpl_id|path|assigner_id|connections|reserved|
        wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id)

        the first three properties are from template_fcp_mapping table,
        and the others are from fcp table. These three properties will
        always have values.

        when the device is not in fcp table, all the properties in fcp
        table will be None. For example: template '12345678' has a fcp
        "1aaa" on path 0, but this device is not in fcp table, the
        query result will be as below.

        1aaa|12345678|0||||||||||

        Note: the FCP id in the returned dict is in uppercase.

        statistics_usage return result format:
        {
            template_id: {
                path1: {},
                path2: {}}

        }
        """

        # get statistic data about:
        # available, allocated, notfound,
        # unallocated_but_active, allocated_but_free
        # CHPIDs
        (fcp_id, template_id, path_id, assigner_id, connections,
         reserved, _, _, chpid, state, owner, _) = raw_item

        # The raw_item is for each fcp device, so there are multiple
        # items for each single FCP Multipath Template.
        # But the return result needs to group all the items by FCP Multipath Template,
        # so construct a dict statistics_usage[template_id]
        # with template_id as key to group the info.
        # template_id key also will be used to join with template base info
        if not statistics_usage.get(template_id, None):
            statistics_usage[template_id] = {}
        if not statistics_usage[template_id].get(path_id, None):
            statistics_usage[template_id][path_id] = {
                "total": [],
                "total_count": 0,
                "single_fcp": [],
                "range_fcp": [],
                "available": [],
                "available_count": 0,
                "allocated": [],
                "reserve_only": [],
                "connection_only": [],
                "unallocated_but_active": {},
                "allocated_but_free": [],
                "notfound": [],
                "offline": [],
                "CHPIDs": {}}
        # when this fcp_id is not None, means the fcp exists in zvm, i.e in
        # fcp table, then it will have detail info from fcp table
        # when this fcp_id is None, means the fcp does not exist in zvm, no
        # detail info, just add into 'not_found' with the tmpl_fcp_id returns
        # from template_fcp_mapping table
        # Show upper case for FCP id
        fcp_id = fcp_id.upper()
        # If a fcp not found in z/VM, will not insert into fcp table, then the
        # db query result will be None. So connections not None represents
        # the fcp is found in z/VM
        if connections is not None:
            # Store each FCP in section "total"
            statistics_usage[template_id][path_id]["total"].append(fcp_id)
            # case G: (state = notfound)
            # this FCP in database but not found in z/VM
            if state == "notfound":
                statistics_usage[
                    template_id][path_id]["notfound"].append(fcp_id)
                LOG.warning("Found a FCP device "
                            "%s in FCP Multipath Template %s, but not found in "
                            "z/VM." % (str(fcp_id), str(template_id)))
            # case H: (state = offline)
            # this FCP in database but offline in z/VM
            if state == "offline":
                statistics_usage[template_id][path_id]["offline"].append(
                    fcp_id)
                LOG.warning("Found state of a FCP "
                            "device %s is offline in database." % str(fcp_id))
            # found this FCP in z/VM
            if connections == 0:
                if reserved == 0:
                    # case A: (reserve=0 and conn=0 and state=free)
                    # this FCP is available for use
                    if state == "free":
                        statistics_usage[
                            template_id][path_id]["available"].append(fcp_id)
                        LOG.debug("Found "
                                  "an available FCP device %s in "
                                  "database." % str(fcp_id))
                    # case E: (conn=0 and reserve=0 and state=active)
                    # this FCP is available in database but its state
                    # is active in smcli output
                    if state == "active":
                        statistics_usage[
                            template_id][path_id]["unallocated_but_active"].\
                            update({fcp_id: owner})
                        LOG.warning("Found a FCP "
                                    "device %s available in database but its "
                                    "state is active, it may be occupied by "
                                    "a userid outside of this ZCC." % str(
                                    fcp_id))
                else:
                    # case C: (reserve=1 and conn=0)
                    # the fcp should be in task or a bug happen
                    statistics_usage[
                        template_id][path_id]["reserve_only"].append(fcp_id)
                    LOG.warning("Found a FCP "
                                "device %s reserve_only." % str(fcp_id))
            else:
                # connections != 0
                if reserved == 0:
                    # case D: (reserve = 0 and conn != 0)
                    # must have a bug result in this
                    statistics_usage[template_id][
                        path_id]["connection_only"].append(fcp_id)
                    LOG.warning("Found a FCP "
                                "device %s unreserved in database but "
                                "its connections is not 0." % str(fcp_id))
                else:
                    # case B: (reserve=1 and conn!=0)
                    # ZCC allocated this to a userid
                    statistics_usage[
                        template_id][path_id]["allocated"].append(fcp_id)
                    LOG.debug("Found an allocated "
                              "FCP device: %s." % str(fcp_id))
                # case F: (conn!=0 and state=free)
                if state == "free":
                    statistics_usage[template_id][
                        path_id]["allocated_but_free"].append(fcp_id)
                    LOG.warning("Found a FCP "
                                "device %s allocated by ZCC but its state is "
                                "free." % str(fcp_id))
                # case I: ((conn != 0) & assigner_id != owner)
                elif assigner_id.lower() != owner.lower() and state != "notfound":
                    LOG.warning("Found a FCP "
                                "device %s allocated by ZCC but its assigner "
                                "differs from owner." % str(fcp_id))
            if chpid:
                if not statistics_usage[template_id][path_id]["CHPIDs"].get(chpid, None):
                    statistics_usage[
                        template_id][path_id]["CHPIDs"].update({chpid: []})
                statistics_usage[
                    template_id][path_id]["CHPIDs"][chpid].append(fcp_id)
        # this FCP in template_fcp_mapping table but not found in z/VM
        else:
            # add into 'total' and 'not_found'
            statistics_usage[template_id][path_id]["total"].append(fcp_id)
            statistics_usage[template_id][path_id]["notfound"].append(fcp_id)
            LOG.warning("Found a FCP device "
                        "%s in FCP Multipath Template %s, but not found in "
                        "z/VM." % (str(fcp_id), str(template_id)))
        return statistics_usage

    def _shrink_fcp_list_in_statistics_usage(self, statistics_usage):
        """shrink fcp list in statistics sections to range fcp
        for example, before shrink:
            template_statistics[path]["total"] = "1A0A, 1A0B, 1A0C, 1A0E"
        after shink:
            template_statistics[path]["total"] = "1A0A - 1A0C, 1A0E"
        """
        for template_statistics in statistics_usage.values():
            for path in template_statistics:
                # count total and available fcp before shrink
                if template_statistics[path]["total"]:
                    template_statistics[path][
                        "total_count"] = len(template_statistics[path][
                                                "total"])
                if template_statistics[path]["available"]:
                    template_statistics[path][
                        "available_count"] = len(template_statistics[path][
                                                    "available"])
                # only below sections in statistics need to shrink
                need_shrink_sections = ["total",
                                        "available",
                                        "allocated",
                                        "reserve_only",
                                        "connection_only",
                                        "allocated_but_free",
                                        "notfound",
                                        "offline"]
                # Do NOT transform unallocated_but_active,
                # because its value also contains VM userid.
                # e.g. [('1b04','owner1'), ('1b05','owner2')]
                # Do NOT transform CHPIDs, total_count, single_fcp,
                # range_fcp and available_count
                for section in need_shrink_sections:
                    fcp_list = template_statistics[path][section]
                    template_statistics[path][section] = (
                        utils.shrink_fcp_list(fcp_list))
                # shrink for each CHIPID
                for chpid, fcps in template_statistics[
                    path]['CHPIDs'].items():
                    fcp_list = fcps
                    template_statistics[path]['CHPIDs'][chpid] = (
                        utils.shrink_fcp_list(fcp_list))

    def _split_singe_range_fcp_list(self, statistics_usage):
        # after shrink, total fcps can have both range and singe fcps,
        # for example: template_statistics[path]['total'] = "1A0A - 1A0C, 1A0E"
        # UI needs 'range_fcp' and 'singe_fcp' to input in different areas
        # so split the total fcps to 'range_fcp' and 'singe_fcp' as below:
        # template_statistics[path]['range_fcp'] = "1A0A - 1A0C"
        # template_statistics[path]['single_fcp'] = "1A0E"
        for template_statistics in statistics_usage.values():
            for path in template_statistics:
                range_fcp = []
                single_fcp = []
                total_fcp = template_statistics[path]['total'].split(',')
                for fcp in total_fcp:
                    if '-' in fcp:
                        range_fcp.append(fcp.strip())
                    else:
                        single_fcp.append(fcp.strip())
                template_statistics[path]['range_fcp'] = ', '.join(range_fcp)
                template_statistics[path]['single_fcp'] = ', '.join(single_fcp)

    def get_fcp_templates(self, template_id_list=None, assigner_id=None,
                          default_sp_list=None, host_default=None):
        """Get template base info by template_id_list or filters
        :param template_id_list: (list) a list of template id,
        if it is None, get FCP Multipath Templates with other parameter
        :param assigner_id: (str) a string of VM userid
        :param default_sp_list: (list) a list of storage provider or 'all',
        to get storage provider's default FCP Multipath Templates

        when sp_host_list = ['all'], will get all storage providers' default
        FCP Multipath Templates. For example, there are 3 FCP Multipath Templates are set as
        storage providers' default template, then all these 3 FCP Multipath Templates
        will return as below:
        {
            "fcp_templates": [
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd2",
                "name": "default_template",
                "description": "This is Default template",
                "host_default": True,
                "storage_providers": [
                    "v7k60",
                    "sp4"
                ]
                },
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd3",
                "name": "test_template",
                "description": "just for test",
                "host_default": False,
                "storage_providers": [
                    "ds8k60c1"
                ]
                },
                {
                "id": "12345678",
                "name": "templatet1",
                "description": "test1",
                "host_default": False,
                "storage_providers": [
                    "sp3"
                ]
                }
            ]
        }

        when sp_host_list is a storage provider name list, will return these
        providers' default FCP Multipath Templates.

        Example:
        sp_host_list = ['v7k60', 'ds8k60c1']

        return:
        {
            "fcp_templates": [
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd2",
                "name": "default_template",
                "description": "This is Default template",
                "host_default": True,
                "storage_providers": [
                    "v7k60",
                    "sp4"
                ]
                },
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd3",
                "name": "test_template",
                "description": "just for test",
                "host_default": False,
                "storage_providers": [
                    "ds8k60c1"
                ]
                }
            ]
        }
        :param host_default: (boolean) whether or not get host default fcp
        template
        :return: (dict) the base info of template
        """
        ret = []

        if template_id_list:
            not_exist = []
            for template_id in template_id_list:
                if not self.db.fcp_template_exist_in_db(template_id):
                    not_exist.append(template_id)
            if not_exist:
                obj_desc = ("FCP Multipath Templates {} ".format(not_exist))
                raise exception.SDKObjectNotExistError(obj_desc=obj_desc)
            raw = self.db.get_fcp_templates(template_id_list)
        elif assigner_id:
            raw = self.db.get_fcp_template_by_assigner_id(assigner_id)
        elif default_sp_list:
            raw = self.db.get_sp_default_fcp_template(default_sp_list)
        elif host_default is not None:
            raw = self.db.get_host_default_fcp_template(host_default)
        else:
            # if no parameter, will get all FCP Multipath Templates
            raw = self.db.get_fcp_templates(template_id_list)

        template_list = self.extract_template_info_from_raw_data(raw)

        for value in template_list.values():
            ret.append(value)
        return {"fcp_templates": ret}

    def get_fcp_templates_details(self, template_id_list=None, raw=False,
                                  statistics=True, sync_with_zvm=False):
        """Get FCP Multipath Templates detail info.
        :param template_list: (list) if is None, will get all the templates on
        the host
        :return: (dict) the raw and/or statistic data of temlate_list FCP
        devices

        if sync_with_zvm:
            self.fcp_mgr._sync_db_with_zvm()
        if FCP DB is NOT empty and raw=True statistics=True
        {
            "fcp_templates":[
                {
                    "id":"36439338-db14-11ec-bb41-0201018b1dd2",
                    "name":"default_template",
                    "description":"This is Default template",
                    "host_default":True,
                    "storage_providers":[
                        "sp4",
                        "v7k60"
                    ],
                    "raw":{
                        # (fcp_id, template_id, assigner_id, connections,
                        #  reserved, wwpn_npiv, wwpn_phy, chpid, state, owner,
                        #  tmpl_id)
                        "0":[
                            [
                                "1a0f",
                                "36439338-db14-11ec-bb41-0201018b1dd2",
                                "HLP0000B",
                                0,
                                0,
                                "c05076de3300038b",
                                "c05076de33002e41",
                                "27",
                                "free",
                                "none",
                                "36439338-db14-11ec-bb41-0201018b1dd2"
                            ],
                            [
                                "1a0e",
                                "36439338-db14-11ec-bb41-0201018b1dd2",
                                "",
                                0,
                                0,
                                "c05076de330003a2",
                                "c05076de33002e41",
                                "27",
                                "free",
                                "none",
                                "36439338-db14-11ec-bb41-0201018b1dd2"
                            ]
                        ],
                        "1":[
                            [
                                "1c0d",
                                "36439338-db14-11ec-bb41-0201018b1dd2",
                                "",
                                0,
                                0,
                                "c05076de33000353",
                                "c05076de33002641",
                                "32",
                                "free",
                                "none",
                                "36439338-db14-11ec-bb41-0201018b1dd2"
                            ]
                        ]
                    },
                    "statistics":{
                        # case A: (reserve = 0 and conn = 0 and state = free)
                        # FCP is available and in free status
                        "available": ('1A00','1A05',...)
                        # case B: (reserve = 1 and conn != 0)
                        # nomral in-use FCP
                        "allocated": ('1B00','1B05',...)
                        # case C: (reserve = 1, conn = 0)
                        # the fcp should be in task or a bug cause this
                        # situation
                        "reserve_only": ('1C00', '1C05', ...)
                        # case D: (reserve = 0 and conn != 0)
                        # should be a bug result in this situation
                        "connection_only": ('1C00', '1C05', ...)
                        # case E: (reserve = 0, conn = 0, state = active)
                        # FCP occupied out-of-band
                        'unallocated_but_active': {'1B04': 'owner1',
                                                   '1B05': 'owner2'}
                        # case F: (conn != 0, state = free)
                        # we allocated it in db but the FCP status is free
                        # this is an situation not expected
                        "allocated_but_free": ('1D00','1D05',...)
                        # case G: (state = notfound)
                        # not found in smcli
                        "notfound": ('1E00','1E05',...)
                        # case H: (state = offline)
                        # offline in smcli
                        "offline": ('1F00','1F05',...)
                        # case I: ((conn != 0) & assigner_id != owner)
                        # assigner_id-in-DB differ from smcli-returned-owner
                        # only log about this
                        # case J: fcp by chpid
                        "0":{
                            "total":"1A0E - 1A0F",
                            "available":"1A0E - 1A0F",
                            "allocated":"",
                            "reserve_only":"",
                            "connection_only":"",
                            "unallocated_but_active":{},
                            "allocated_but_free":"",
                            "notfound":"",
                            "offline":"",
                            "CHPIDs":{
                                "27":"1A0E - 1A0F"
                            }
                        },
                        "1":{
                            "total":"1C0D",
                            "available":"1C0D",
                            "allocated":"",
                            "reserve_only":"",
                            "connection_only":"",
                            "unallocated_but_active":{},
                            "allocated_but_free":"",
                            "notfound":"",
                            "offline":"",
                            "CHPIDs":{
                                "32":"1C0D"
                            }
                        }
                    }
                }
            ]
        }
        """
        not_exist = []
        if template_id_list:
            for template_id in template_id_list:
                if not self.db.fcp_template_exist_in_db(template_id):
                    not_exist.append(template_id)
        if not_exist:
            obj_desc = ("FCP Multipath Templates {} ".format(not_exist))
            raise exception.SDKObjectNotExistError(obj_desc=obj_desc)

        if sync_with_zvm:
            self._sync_db_with_zvm()
        statistics_usage = {}
        raw_usage = {}
        template_info = {}
        ret = []

        # tmpl_cmd result format:
        # [(id|name|description|is_default|sp_name)]

        # devices_cmd result format:
        # [(fcp_id|tmpl_id|path|assigner_id|connections|reserved|
        # wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id)]

        tmpl_result, devices_result = self.db.get_fcp_templates_details(
            template_id_list)

        # extract template base info into template_info
        template_info = self.extract_template_info_from_raw_data(tmpl_result)
        # template_info foramt:
        # {
        #     temlate_id: {
        #         "id": id,
        #         "name": name,
        #         "description": description,
        #         "is_default": is_default,
        #         "storage_providers": [sp_name]
        #     }
        # }
        if raw:
            for item in devices_result:
                self._update_template_fcp_raw_usage(raw_usage, item)
            for template_id, base_info in template_info.items():
                if template_id in raw_usage:
                    base_info.update({"raw": raw_usage[template_id]})
                else:
                    # some template does not have fcp devices, so there is no
                    # raw_usage for such template
                    base_info.update({"raw": {}})
            # after join raw info, template_info format is like this:
            # {
            #     temlate_id: {
            #         "id": id,
            #         "name": name,
            #         "description": description,
            #         "is_default": is_default,
            #         "storage_providers": [sp_name],
            #          "raw": {
            #              path1: {},
            #              path2: {}}
            #          }
            #   }
            # }
        # get fcp statistics usage
        if statistics:
            for item in devices_result:
                self._update_template_fcp_statistics_usage(
                    statistics_usage, item)
            LOG.info("statistic FCP usage before shrink: %s"
                     % statistics_usage)
            self._shrink_fcp_list_in_statistics_usage(statistics_usage)
            self._split_singe_range_fcp_list(statistics_usage)
            LOG.info("statistic FCP usage after shrink: %s"
                     % statistics_usage)
            # update base info with statistics_usage
            # statistics_usage format:
            # {
            #     template_id1: {
            #         path1: {},
            #         path2: {}},
            #     template_id2: {
            #         path1: {},
            #         path2: {}}
            # }
            for template_id, base_info in template_info.items():
                # only the FCP Multipath Template which has fcp in zvm has
                # statistics_usage data
                if template_id in statistics_usage:
                    base_info.update(
                        {"statistics": statistics_usage[template_id]})
                else:
                    # some templates do not have fcp devices or do not have
                    # valid fcp in zvm, so do not have statistics_usage data
                    base_info.update({"statistics": {}})
            # after join statistics info, template_info format is like this:
            # {
            #     temlate_id: {
            #         "id": id,
            #         "name": name,
            #         "description": description,
            #         "host_default": is_default,
            #         "storage_providers": [sp_name],
            #          "statistics": {
            #              path1: {},
            #              path2: {}}
            #          }
            #   }
            # }
        for value in template_info.values():
            ret.append(value)
        return {"fcp_templates": ret}

    def delete_fcp_template(self, template_id):
        """Delete FCP Multipath Template by id.
        :param template_id: (str)
        :return: no return result
        """
        return self.db.delete_fcp_template(template_id)


# volume manager for FCP protocol
class FCPVolumeManager(object):
    def __init__(self):
        self.fcp_mgr = FCPManager()
        self.config_api = VolumeConfiguratorAPI()
        self._smtclient = smtclient.get_smtclient()
        self._lock = threading.RLock()
        # previously FCPDbOperator is initialized twice, here we
        # just do following variable redirection to avoid too much
        # reference code changes
        self.db = self.fcp_mgr.db

    def _dedicate_fcp(self, fcp, assigner_id):
        self._smtclient.dedicate_device(assigner_id, fcp, fcp, 0)

    def _add_disks(self, fcp_list, assigner_id, target_wwpns, target_lun,
                   multipath, os_version, mount_point):
        self.config_api.config_attach(fcp_list, assigner_id, target_wwpns,
                                      target_lun, multipath, os_version,
                                      mount_point)

    def _rollback_reserved_fcp_devices(self, fcp_list):
        """
        Rollback for the following completed operations:
            operations on FCP DB done by get_volume_connector()
            i.e. reserve FCP device and set FCP Multipath Template id from FCP DB

        :param fcp_list: (list) a list of FCP devices
        :return: None
        """
        LOG.info("Enter rollback function: _rollback_reserved_fcp_devices.")
        # Before rollback, print information for debug
        fcp_usage = [self.get_fcp_usage(fcp) for fcp in fcp_list]
        LOG.info("Before rollback, the usage of the FCP devices is: %s" % fcp_usage)
        # Get the connections status in FCP DB
        fcp_connections = {fcp: self.db.get_connections_from_fcp(fcp)
                           for fcp in fcp_list}
        # Operation on FCP DB:
        # if connections is 0,
        # then unreserve the FCP device and cleanup tmpl_id
        no_connection_fcps = [fcp for fcp in fcp_connections
                              if fcp_connections[fcp] == 0]
        if no_connection_fcps:
            with zvmutils.ignore_errors():
                self.db.unreserve_fcps(no_connection_fcps)
                LOG.info("Rollback on FCP DB: Unreserve FCP devices %s", no_connection_fcps)
        # After rollback, print information for debug
        fcp_usage = [self.get_fcp_usage(fcp) for fcp in fcp_list]
        LOG.info("After rollback, the usage of the FCP devices is: %s" % fcp_usage)
        LOG.info("Exit rollback function: _rollback_reserved_fcp_devices.")

    def _rollback_increased_connections(self, fcp_list):
        """
        Rollback for the following completed operations:
            operations on FCP DB done by increase_fcp_connections() that
            set connections +1 in FCP DB.

        :param fcp_list: (list) a list of FCP devices
        :return: None
        """
        LOG.info("Enter rollback function: _rollback_increased_connections")
        # Before rollback, print information for debug
        fcp_usage = [self.get_fcp_usage(fcp) for fcp in fcp_list]
        LOG.info("Before rollback, the usage of the FCP devices is: %s" % fcp_usage)
        for fcp in fcp_list:
            with zvmutils.ignore_errors():
                self.db.decrease_connections(fcp)
        # After rollback, print information for debug
        fcp_usage = [self.get_fcp_usage(fcp) for fcp in fcp_list]
        LOG.info("After rollback, the usage of the FCP devices is: %s" % fcp_usage)
        LOG.info("Exit rollback function: _rollback_increased_connections")

    def _rollback_dedicated_fcp_devices(self, fcp_list, assigner_id):
        """
        Rollback for the following completed operations:
            operations on z/VM done by _dedicate_fcp()
            i.e. dedicate FCP device from assigner_id

        :param fcp_list: (list) a list of FCP devices
        :param assigner_id: (str) the userid of the virtual machine
        :return: None
        """
        LOG.info("Enter rollback function: _rollback_dedicated_fcp_devices")
        # Get the connections status in FCP DB
        fcp_connections = {fcp: self.db.get_connections_from_fcp(fcp)
                           for fcp in fcp_list}
        # Operation on z/VM:
        # undedicate FCP device from assigner_id
        for fcp in fcp_list:
            with zvmutils.ignore_errors():
                if fcp_connections[fcp] == 0:
                    self._undedicate_fcp(fcp, assigner_id)
                    LOG.info("Rollback on z/VM: undedicate FCP device: %s" % fcp)
        LOG.info("Exit rollback function: _rollback_dedicated_fcp_devices")

    def _rollback_added_disks(self, fcp_list, assigner_id, target_wwpns, target_lun,
                              multipath, os_version, mount_point):
        """
        Rollback for the following completed operations:
            operation on VM operating system done by _add_disks()
            i.e. online FCP devices and the volume from VM OS

        :param fcp_list: (list) a list of FCP devices
        :param assigner_id: (str) the userid of the virtual machine
        :return: None
        """
        LOG.info("Enter rollback function: _rollback_added_disks")
        # Operation on VM OS: offline volume and FCP devices from VM OS
        fcp_connections = {fcp: self.db.get_connections_from_fcp(fcp)
                           for fcp in fcp_list}
        with zvmutils.ignore_errors():
            # _remove_disks() offline FCP devices only when total_connections is 0,
            # i.e. detaching the last volume from the FCP devices
            total_connections = sum(fcp_connections.values())
            self._remove_disks(fcp_list, assigner_id, target_wwpns, target_lun,
                               multipath, os_version, mount_point, total_connections)
            LOG.info("Rollback on VM OS: offline the volume from VM OS")
        LOG.info("Exit rollback function: _rollback_added_disks")

    def _do_attach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                   multipath, os_version, mount_point, is_root_volume,
                   fcp_template_id):
        """Attach a volume

        First, we need translate fcp into local wwpn, then
        dedicate fcp to the user if it's needed, after that
        call smt layer to configure volume in the target VM.
        """
        LOG.info("Start to attach volume to FCP devices "
                 "%s on machine %s." % (fcp_list, assigner_id))
        try:
            # Operation on FCP DB:
            # 1. Although the fcp devices in fcp_list were already reserved by get_volume_connector,
            #    in case some concurrent thread did _rollback_reserved_fcp_devices later,
            #    here need to reserve those FCP devices in DB again.
            self.fcp_mgr.reserve_fcp_devices(fcp_list, assigner_id, fcp_template_id)
            # 2. increase connections by 1 and set assigner_id.
            # fcp_connections examples:
            # {'1a10': 1, '1b10': 1} => attaching 1st volume
            # {'1a10': 2, '1b10': 2} => attaching 2nd volume
            # {'1a10': 2, '1b10': 1} => connections differ in abnormal case (due to bug)
            # the values are the connections of the FCP device
            fcp_connections = self.fcp_mgr.increase_fcp_connections(fcp_list, assigner_id)
            LOG.info("The connections of FCP devices before "
                     "being dedicated to virtual machine %s is: %s."
                     % (assigner_id, fcp_connections))
        except Exception as err:
            LOG.error("Failed to increase connections of the FCP devices on %s in "
                      "database because %s." % (assigner_id, str(err)))
            # Rollback for the following completed operations:
            # 1. operations on FCP DB done by get_volume_connector() and reserve_fcp_devices()
            # No need to rollback the connections in FCP DB because
            # the increase_fcp_connections will rollback them automatically.
            self._rollback_reserved_fcp_devices(fcp_list)
            raise

        if is_root_volume:
            LOG.info("We are attaching root volume, dedicating FCP devices %s "
                     "to virtual machine %s has been done by refresh_bootmap; "
                     "skip the remain steps of volume attachment."
                     % (fcp_list, assigner_id))
            return []

        # Operation on z/VM: dedicate FCP devices to the assigner_id in z/VM
        try:
            for fcp in fcp_list:
                # Dedicate the FCP device on z/VM only when connections are 1,
                # which means this is 1st volume attached to this FCP device,
                # otherwise the FCP device has been dedicated already.
                # if _dedicate_fcp() raise exception for an FCP device, we must stop
                # the whole attachment to go to except-block to do rollback operations.
                if fcp_connections[fcp] == 1:
                    LOG.info("Start to dedicate FCP %s to "
                             "%s in z/VM." % (fcp, assigner_id))
                    # dedicate the FCP to the assigner in z/VM
                    self._dedicate_fcp(fcp, assigner_id)
                    LOG.info("Dedicating FCP %s to %s in z/VM is "
                             "done." % (fcp, assigner_id))
                else:
                    LOG.info("This is not the first time to "
                             "attach volume to FCP %s, "
                             "skip dedicating the FCP device in z/VM." % fcp)
        except Exception as err:
            LOG.error("Failed to dedicate FCP devices to %s in "
                      "z/VM because %s." % (assigner_id, str(err)))
            # Rollback for the following completed operations:
            # 1. operations on z/VM done by _dedicate_fcp()
            # 2. operations on FCP DB done by increase_fcp_connections()
            # 3. operations on FCP DB done by get_volume_connector() and reserve_fcp_devices()
            self._rollback_dedicated_fcp_devices(fcp_list, assigner_id)
            self._rollback_increased_connections(fcp_list)
            self._rollback_reserved_fcp_devices(fcp_list)
            raise

        # Operation on VM operating system: online the volume in the virtual machine
        try:
            LOG.info("Start to configure volume in the operating "
                     "system of %s." % assigner_id)
            self._add_disks(fcp_list, assigner_id, target_wwpns,
                            target_lun, multipath, os_version,
                            mount_point)
            LOG.info("Configuring volume in the operating "
                     "system of %s is done." % assigner_id)
            LOG.info("Attaching volume to FCP devices %s on virtual machine %s is "
                     "done." % (fcp_list, assigner_id))
        except Exception as err:
            LOG.error("Failed to configure volume in the OS of %s "
                      "because %s." % (assigner_id, str(err)))
            # Rollback for the following completed operations:
            # 1. operations on VM OS done by _add_disks()
            # 2. operations on z/VM done by _dedicate_fcp()
            # 3. operations on FCP DB done by increase_fcp_connections()
            # 4. operations on FCP DB done by get_volume_connector() and reserve_fcp_devices()
            self._rollback_added_disks(fcp_list, assigner_id, target_wwpns, target_lun,
                                       multipath, os_version, mount_point)
            self._rollback_dedicated_fcp_devices(fcp_list, assigner_id)
            self._rollback_increased_connections(fcp_list)
            self._rollback_reserved_fcp_devices(fcp_list)
            raise

    def _rollback_decreased_connections(self, fcp_list, assigner_id):
        """
        Rollback for the following completed operations:
            operations on FCP DB done by decrease_fcp_connections() that
            set connections +1 in FCP DB.

        :param fcp_list: (list) a list of FCP devices
        :return: None
        """
        LOG.info("Enter rollback function: _rollback_decreased_connections")
        # Before rollback, print information for debug
        fcp_usage = [self.get_fcp_usage(fcp) for fcp in fcp_list]
        LOG.info("Before rollback, the usage of the FCP devices is: %s" % fcp_usage)
        for fcp in fcp_list:
            with zvmutils.ignore_errors():
                self.db.increase_connections_by_assigner(fcp, assigner_id)
        # After rollback, print information for debug
        fcp_usage = [self.get_fcp_usage(fcp) for fcp in fcp_list]
        LOG.info("After rollback, the usage of the FCP devices is: %s" % fcp_usage)
        LOG.info("Exit rollback function: _rollback_decreased_connections")

    def _rollbck_undedicated_fcp_devices(self, fcp_connections, assigner_id):
        """
        Rollback for the following completed operations:
            operations on z/VM done by _undedicate_fcp()
            i.e. undedicate FCP device from assigner_id

        :param fcp_list: (list) a list of FCP devices
        :param assigner_id: (str) the userid of the virtual machine
        :return: None
        """
        LOG.info("Enter rollback function: _rollbck_undedicated_fcp_devices")
        # Operation on z/VM: dedicate FCP devices to the virtual machine
        for fcp in fcp_connections:
            with zvmutils.ignore_errors():
                # _undedicate_fcp() has been done in _do_detach() if fcp_connections[fcp] == 0,
                # so we do _dedicate_fcp() as rollback with the same if-condition
                if fcp_connections[fcp] == 0:
                    # dedicate the FCP to the assigner in z/VM
                    self._dedicate_fcp(fcp, assigner_id)
                    LOG.info("Rollback on z/VM: dedicate FCP device: %s" % fcp)
        LOG.info("Exit rollback function: _rollbck_undedicated_fcp_devices")

    def _rollback_removed_disks(self, fcp_connections, assigner_id, target_wwpns, target_lun,
                                multipath, os_version, mount_point):
        """
        Rollback for the following completed operations:
           operation on VM operating system done by _remove_disks()
           i.e. remove FCP devices and the volume from VM OS

        :param fcp_list: (list) a list of FCP devices
        :param assigner_id: (str) the userid of the virtual machine
        :return: None
        """
        LOG.info("Enter rollback function: _rollback_removed_disks")
        # Operation on VM operating system:
        # online the volume in the virtual machine
        with zvmutils.ignore_errors():
            fcp_list = [f for f in fcp_connections]
            self._add_disks(fcp_list, assigner_id,
                            target_wwpns, target_lun,
                            multipath, os_version, mount_point)
            LOG.info("Rollback on VM operating system: "
                     "online volume for virtual machine %s"
                     % assigner_id)
        LOG.info("Exit rollback function: _rollback_removed_disks")

    def volume_refresh_bootmap(self, fcpchannels, wwpns, lun,
                               wwid='',
                               transportfiles=None, guest_networks=None,
                               fcp_template_id=None):
        if not fcp_template_id:
            min_fcp_paths_count = len(fcpchannels)
        else:
            min_fcp_paths_count = self.db.get_min_fcp_paths_count(fcp_template_id)
            if min_fcp_paths_count == 0:
                errmsg = ("No FCP devices were found in the FCP Multipath Template %s,"
                          "stop refreshing bootmap." % fcp_template_id)
                LOG.error(errmsg)
                raise exception.SDKBaseException(msg=errmsg)
        with zvmutils.acquire_lock(self._lock):
            LOG.debug('Enter lock scope of volume_refresh_bootmap.')
            ret = self._smtclient.volume_refresh_bootmap(fcpchannels, wwpns,
                                                         lun, wwid=wwid,
                                                         transportfiles=transportfiles,
                                                         guest_networks=guest_networks,
                                                         min_fcp_paths_count=min_fcp_paths_count)
        LOG.debug('Exit lock of volume_refresh_bootmap with ret %s.' % ret)
        return ret

    @utils.synchronized('volumeAttachOrDetach-{connection_info[assigner_id]}')
    def attach(self, connection_info):
        """Attach a volume to a guest

        connection_info contains info from host and storage side
        this mostly includes
        host side FCP: this can get host side wwpn
        storage side wwpn
        storage side lun

        all the above assume the storage side info is given by caller
        """
        fcps = connection_info['zvm_fcp']
        wwpns = connection_info['target_wwpn']
        target_lun = connection_info['target_lun']
        assigner_id = connection_info['assigner_id'].upper()
        multipath = connection_info['multipath'].lower()
        if multipath == 'true':
            multipath = True
        else:
            multipath = False
        os_version = connection_info['os_version']
        mount_point = connection_info['mount_point']
        is_root_volume = connection_info.get('is_root_volume', False)
        fcp_template_id = connection_info['fcp_template_id']

        if is_root_volume is False and \
                not zvmutils.check_userid_exist(assigner_id):
            LOG.error("The virtual machine '%s' does not exist on z/VM." % assigner_id)
            raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % assigner_id), modID='volume')
        else:
            # transfer to lower cases
            fcp_list = [x.lower() for x in fcps]
            target_wwpns = [wwpn.lower() for wwpn in wwpns]
            try:
                self._do_attach(fcp_list, assigner_id,
                                target_wwpns, target_lun,
                                multipath, os_version,
                                mount_point, is_root_volume,
                                fcp_template_id)
            except Exception:
                for fcp in fcp_list:
                    with zvmutils.ignore_errors():
                        _userid, _reserved, _conns, _tmpl_id = self.get_fcp_usage(fcp)
                        LOG.info("After rollback, property of FCP device %s "
                                 "is (assigner_id: %s, reserved:%s, "
                                 "connections: %s, FCP Multipath Template id: %s)."
                                 % (fcp, _userid, _reserved, _conns, _tmpl_id))
                raise

    def _undedicate_fcp(self, fcp, assigner_id):
        try:
            self._smtclient.undedicate_device(assigner_id, fcp)
        except exception.SDKSMTRequestFailed as err:
            rc = err.results['rc']
            rs = err.results['rs']
            if (rc == 404 or rc == 204) and rs == 8:
                # We ignore the two exceptions raised when FCP device is already undedicated.
                # Example of exception when rc == 404:
                #   zvmsdk.exception.SDKSMTRequestFailed:
                #   Failed to undedicate device from userid 'JACK0003'.
                #   RequestData: 'changevm JACK0003 undedicate 1d1a',
                #   Results: '{'overallRC': 8,
                #       'rc': 404, 'rs': 8, 'errno': 0,
                #       'strError': 'ULGSMC5404E Image device not defined',
                #       'response': ['(Error) ULTVMU0300E
                #           SMAPI API failed: Image_Device_Undedicate_DM,
                # Example of exception when rc == 204:
                #   zvmsdk.exception.SDKSMTRequestFailed:
                #   Failed to undedicate device from userid 'JACK0003'.
                #   RequestData: 'changevm JACK0003 undedicate 1b17',
                #   Results: '{'overallRC': 8,
                #       'rc': 204, 'rs': 8, 'errno': 0,
                #       'response': ['(Error) ULTVMU0300E
                #           SMAPI API failed: Image_Device_Undedicate,
                msg = ('ignore an exception because the FCP device {} '
                       'has already been undedicdated on z/VM: {}'
                       ).format(fcp, err.format_message())
                LOG.warn(msg)
            else:
                # raise exception
                raise

    def _remove_disks(self, fcp_list, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point, connections):
        self.config_api.config_detach(fcp_list, assigner_id, target_wwpns,
                                      target_lun, multipath, os_version,
                                      mount_point, connections)

    def _do_detach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                   multipath, os_version, mount_point, is_root_volume,
                   update_connections_only):
        """Detach a volume from a guest"""
        LOG.info("Start to detach volume on virtual machine %s from "
                 "FCP devices %s" % (assigner_id, fcp_list))

        # Operation on FCP DB: decrease connections by 1
        # fcp_connections is like {'1a10': 0, '1b10': 2}
        # the values are the connections of the FCP devices.
        fcp_connections = self.fcp_mgr.decrease_fcp_connections(fcp_list)

        # If is root volume we only need update database records
        # because the dedicate operations are done by volume_refresh_bootmap.
        # If update_connections set to True, means upper layer want
        # to update database record only. For example, try to delete
        # the instance, then no need to waste time on undedicate.
        if is_root_volume or update_connections_only:
            if update_connections_only:
                LOG.info("Update connections only, undedicating FCP devices %s "
                         "from virtual machine %s has been done; skip the remain "
                         "steps of volume detachment" % (fcp_list, assigner_id))
            else:
                LOG.info("We are detaching root volume, undedicating FCP devices %s "
                         "from virtual machine %s has been done; skip the remain "
                         "steps of volume detachment" % (fcp_list, assigner_id))
            return

        # when detaching volumes, if userid not exist, no need to
        # raise exception. We stop here after the database operations done.
        if not zvmutils.check_userid_exist(assigner_id):
            LOG.warning("Virtual machine %s does not exist when trying to detach "
                        "volume from it. skip the remain steps of volume "
                        "detachment", assigner_id)
            return

        # Operation on VM operating system: offline the volume in the virtual machine
        try:
            LOG.info("Start to remove volume in the operating "
                     "system of %s." % assigner_id)
            # Case1: this volume is NOT the last volume of this VM.
            #   The connections of all the FCP devices are non-zero normally, for example:
            #       sum(fcp_connections.values()) > 0
            #       fcp_connections is like {'1a10': 2, '1b10': 2}
            #   In this case, _remove_disks() must be called with total_connections > 0,
            #   so as NOT to offline the FCP devices from VM Linux operating system.
            # Case2: this volume is the last volume of this VM.
            #   the connections of all the FCP devices are non-zero normally, for example:
            #       sum(fcp_connections.values()) == 0,
            #       fcp_connections is like {'1a10': 0, '1b10': 0}
            #   In this case, _remove_disks() must be called with total_connections as 0,
            #   so as to offline the FCP devices from VM Linux operating system.
            # Case3: the connections of partial FCPs are 0, for example:
            #   sum(fcp_connections.values()) > 0
            #   fcp_connections is like {'1a10': 0, '1b10': 3}
            #   In this case, _remove_disks() must be called with total_connections > 0,
            #   so as NOT to offline the FCP devices from VM Linux operating system.
            total_connections = sum(fcp_connections.values())
            self._remove_disks(fcp_list, assigner_id, target_wwpns, target_lun,
                               multipath, os_version, mount_point, total_connections)
            LOG.info("Removing volume in the operating "
                     "system of %s is done." % assigner_id)
        except Exception as err:
            LOG.error("Failed to remove disks in the OS of %s because %s." % (assigner_id, str(err)))
            self._rollback_removed_disks(fcp_connections, assigner_id, target_wwpns, target_lun,
                                         multipath, os_version, mount_point)
            self._rollback_decreased_connections(fcp_list, assigner_id)
            raise

        # Operation on z/VM: undedicate FCP device from the virtual machine
        try:
            for fcp in fcp_list:
                if fcp_connections[fcp] == 0:
                    # As _remove_disks() has been run successfully,
                    # we need to try our best to undedicate every FCP device
                    LOG.info("Start to undedicate FCP %s from "
                             "%s on z/VM." % (fcp, assigner_id))
                    self._undedicate_fcp(fcp, assigner_id)
                    LOG.info("FCP %s undedicated from %s on z/VM is "
                         "done." % (fcp, assigner_id))
                else:
                    LOG.info("The connections of FCP device %s is not 0, "
                             "skip undedicating the FCP device on z/VM." % fcp)
            LOG.info("Detaching volume on virtual machine %s from FCP devices %s is "
                     "done." % (assigner_id, fcp_list))
        except Exception as err:
            LOG.error("Failed to undedicate the FCP devices on %s because %s." % (assigner_id, str(err)))
            # Rollback for the following completed operations:
            # 1. operations on z/VM done by _udedicate_fcp()
            # 2. operations on VM OS done by _remove_disks()
            # 3. operations on FCP DB done by decrease_fcp_connections()
            self._rollbck_undedicated_fcp_devices(fcp_connections, assigner_id)
            self._rollback_removed_disks(fcp_connections, assigner_id, target_wwpns, target_lun,
                                         multipath, os_version, mount_point)
            self._rollback_decreased_connections(fcp_list, assigner_id)
            raise

    @utils.synchronized('volumeAttachOrDetach-{connection_info[assigner_id]}')
    def detach(self, connection_info):
        """Detach a volume from a guest
        """
        fcps = connection_info['zvm_fcp']
        wwpns = connection_info['target_wwpn']
        target_lun = connection_info['target_lun']
        assigner_id = connection_info['assigner_id'].upper()
        multipath = connection_info['multipath'].lower()
        os_version = connection_info['os_version']
        mount_point = connection_info['mount_point']
        if multipath == 'true':
            multipath = True
        else:
            multipath = False

        is_root_volume = connection_info.get('is_root_volume', False)
        update_connections_only = connection_info.get(
                'update_connections_only', False)
        # transfer to lower cases
        fcp_list = [x.lower() for x in fcps]
        target_wwpns = [wwpn.lower() for wwpn in wwpns]
        try:
            self._do_detach(fcp_list, assigner_id,
                            target_wwpns, target_lun,
                            multipath, os_version, mount_point,
                            is_root_volume, update_connections_only)
        except Exception:
            for fcp in fcp_list:
                with zvmutils.ignore_errors():
                    _userid, _reserved, _conns, _tmpl_id = self.get_fcp_usage(fcp)
                    LOG.info("After rollback, property of FCP device %s "
                             "is (assigner_id: %s, reserved:%s, "
                             "connections: %s, FCP Multipath Template id: %s)."
                             % (fcp, _userid, _reserved, _conns, _tmpl_id))
            raise

    @utils.synchronized('volumeAttachOrDetach-{assigner_id}')
    def get_volume_connector(self, assigner_id, reserve,
                             fcp_template_id=None, sp_name=None):
        """Get connector information of the instance for attaching to volumes.

        Connector information is a dictionary representing the Fibre
        Channel(FC) port(s) that will be making the connection.
        The properties of FC port(s) are as follows::
        {
            'zvm_fcp': [fcp1, fcp2]
            'wwpns': [npiv_wwpn1, npiv_wwpn2]
            'phy_to_virt_initiators':{
                npiv_wwpn1: phy_wwpn1,
                npiv_wwpn2: phy_wwpn2,
            }
            'host': LPARname_VMuserid,
            'fcp_paths': 2,            # the count of fcp paths
            'fcp_template_id': fcp_template_id # if user doesn't specify it,
                               it is either the SP default or the host
                               default template id
        }
        """
        with database.get_fcp_conn():
            if fcp_template_id and \
                    not self.db.fcp_template_exist_in_db(fcp_template_id):
                errmsg = ("fcp_template_id %s doesn't exist." % fcp_template_id)
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(
                    rs=11, userid=assigner_id, msg=errmsg)

            # get lpar name of the userid,
            # if no host name got, raise exception
            zvm_host = zvmutils.get_lpar_name()
            if zvm_host == '':
                errmsg = "failed to get z/VM LPAR name."
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(
                    rs=11, userid=assigner_id, msg=errmsg)
            """
            Reserve or unreserve FCP device
            according to assigner id and FCP Multipath Template id.
            """
            if reserve:
                LOG.info("get_volume_connector: Enter allocate_fcp_devices.")
                # The data structure of fcp_list is:
                # [(fcp_id, wwpn_npiv, wwpn_phy)]
                fcp_list, fcp_template_id = self.fcp_mgr.allocate_fcp_devices(
                    assigner_id, fcp_template_id, sp_name)
                LOG.info("get_volume_connector: Exit allocate_fcp_devices {}".format(
                    [f['fcp_id'] for f in fcp_list]))
            else:
                LOG.info("get_volume_connector: Enter release_fcp_devices.")
                # The data structure of fcp_list is:
                # [(fcp_id, wwpn_npiv, wwpn_phy, connections)]
                # An example of fcp_list:
                # [('1c10', 'c12345abcdefg1', 'c1234abcd33002641', 1),
                #  ('1d10', 'c12345abcdefg2', 'c1234abcd33002641', 0)]
                fcp_list = self.fcp_mgr.release_fcp_devices(
                    assigner_id, fcp_template_id)
                LOG.info("get_volume_connector: Exit release_fcp_devices {}".format(
                    [f['fcp_id'] for f in fcp_list]))

        empty_connector = {'zvm_fcp': [],
                           'wwpns': [],
                           'host': '',
                           'phy_to_virt_initiators': {},
                           'fcp_paths': 0,
                           'fcp_template_id': fcp_template_id}
        if not fcp_list:
            errmsg = ("Not enough available FCP devices found from "
                      "FCP Multipath Template(id={})".format(fcp_template_id))
            LOG.error(errmsg)
            return empty_connector

        # get wwpns of fcp devices
        wwpns = []
        phy_virt_wwpn_map = {}
        fcp_ids = []
        for fcp in fcp_list:
            wwpn_npiv = fcp[1]
            fcp_ids.append(fcp[0])
            wwpns.append(wwpn_npiv)
            phy_virt_wwpn_map[wwpn_npiv] = fcp[2]

        # return the LPARname+VMuserid as host
        ret_host = zvm_host + '_' + assigner_id
        connector = {'zvm_fcp': fcp_ids,
                     'wwpns': wwpns,
                     'phy_to_virt_initiators': phy_virt_wwpn_map,
                     'host': ret_host,
                     'fcp_paths': len(fcp_list),
                     'fcp_template_id': fcp_template_id}
        LOG.info('get_volume_connector returns %s for '
                 'assigner %s and FCP Multipath Template %s'
                 % (connector, assigner_id, fcp_template_id))
        return connector

    def check_fcp_exist_in_db(self, fcp, raise_exec=True):
        all_fcps_raw = self.db.get_all()
        all_fcps = []
        for item in all_fcps_raw:
            all_fcps.append(item[0].lower())
        if fcp not in all_fcps:
            if raise_exec:
                LOG.error("fcp %s not exist in db!", fcp)
                raise exception.SDKObjectNotExistError(
                    obj_desc=("FCP '%s'" % fcp), modID='volume')
            else:
                LOG.warning("fcp %s not exist in db!", fcp)
                return False
        else:
            return True

    def get_fcp_usage(self, fcp):
        userid, reserved, connections, tmpl_id = self.db.get_usage_of_fcp(fcp)
        LOG.debug("Got userid:%s, reserved:%s, connections:%s, tmpl_id: %s "
                  "of FCP:%s" % (userid, reserved, connections, fcp, tmpl_id))
        return userid, reserved, connections, tmpl_id

    def set_fcp_usage(self, fcp, assigner_id, reserved, connections,
                      fcp_template_id):
        self.db.update_usage_of_fcp(fcp, assigner_id, reserved, connections,
                                    fcp_template_id)
        LOG.info("Set usage of fcp %s to userid:%s, reserved:%s, "
                 "connections:%s, tmpl_id: %s." % (fcp, assigner_id,
                                                   reserved, connections,
                                                   fcp_template_id))
