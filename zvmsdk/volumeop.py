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
import string

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import database
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import smtclient
from zvmsdk import utils as zvmutils
from zvmsdk import vmops


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

_LOCK_RESERVE_FCP = threading.RLock()


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
                               transportfiles='', guest_networks=None):
        return self._volume_manager.volume_refresh_bootmap(fcpchannel, wwpn,
                                            lun, wwid=wwid,
                                            transportfiles=transportfiles,
                                            guest_networks=guest_networks)

    def get_volume_connector(self, assigner_id, reserve, fcp_template_id=None):
        return self._volume_manager.get_volume_connector(assigner_id, reserve, fcp_template_id=fcp_template_id)

    def check_fcp_exist_in_db(self, fcp, raise_exec=True):
        return self._volume_manager.check_fcp_exist_in_db(fcp, raise_exec)

    def get_all_fcp_usage(self, assigner_id=None, raw=False, statistics=True,
                          sync_with_zvm=False):
        return self._volume_manager.get_all_fcp_usage(
                assigner_id, raw=raw, statistics=statistics,
                sync_with_zvm=sync_with_zvm)

    def get_fcp_usage(self, fcp):
        return self._volume_manager.get_fcp_usage(fcp)

    def set_fcp_usage(self, assigner_id, fcp, reserved, connections):
        return self._volume_manager.set_fcp_usage(fcp, assigner_id,
                                                  reserved, connections)

    def create_fcp_template(self, name, description, fcp_devices,
                            host_default: bool = False,
                            default_sp_list: list = None):
        return self._volume_manager.fcp_mgr.create_fcp_template(
            name, description, fcp_devices, host_default, default_sp_list)

    def get_fcp_templates(self, template_id_list=None, assigner_id=None,
                          default_sp_list=None, host_default=False):
        return self._volume_manager.fcp_mgr.get_fcp_templates(
            template_id_list, assigner_id, default_sp_list, host_default)

    def get_fcp_templates_details(self, template_id_list=None, raw=False,
                                  statistics=True, sync_with_zvm=False):
        return self._volume_manager.fcp_mgr.get_fcp_templates_details(
            template_id_list, raw=raw, statistics=statistics,
            sync_with_zvm=sync_with_zvm)


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
                 "target machine %s with FCP devices "
                 "%s." % (target_wwpns, target_lun, assigner_id, fcp_list))
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        self.configure_volume_attach(fcp_list, assigner_id, target_wwpns,
                                     target_lun, multipath, os_version,
                                     mount_point, linuxdist)
        iucv_is_ready = self.check_IUCV_is_ready(assigner_id)
        if iucv_is_ready:
            # active mode should restart zvmguestconfigure to run reader file
            active_cmds = linuxdist.create_active_net_interf_cmd()
            ret = self._smtclient.execute_cmd_direct(
                assigner_id, active_cmds,
                timeout=CONF.volume.punch_script_execution_timeout)
            LOG.debug('attach scripts return values: %s' % ret)
            if ret['rc'] != 0:
                # if return code is 64 means timeout
                # no need to check the exist code of systemctl and return
                if ret['rc'] == 64:
                    errmsg = ('attach script execution in the target machine '
                              '%s for volume (WWPN:%s, LUN:%s) '
                              'exceed the timeout %s.'
                              % (assigner_id, target_wwpns, target_lun,
                                 CONF.volume.punch_script_execution_timeout))
                    LOG.error(errmsg)
                    raise exception.SDKVolumeOperationError(
                        rs=8, userid=assigner_id, msg=errmsg)
                # get exit code by systemctl status
                get_status_cmd = 'systemctl status zvmguestconfigure.service'
                exit_code = self._get_status_code_from_systemctl(
                    assigner_id, get_status_cmd)
                if exit_code == 1:
                    errmsg = ('attach script execution failed because the '
                              'volume (WWPN:%s, LUN:%s) did not show up in '
                              'the target machine %s , please check its '
                              'connections.' % (target_wwpns, target_lun,
                                                assigner_id))
                else:
                    errmsg = ('attach script execution in the target machine '
                              '%s for volume (WWPN:%s, LUN:%s) '
                              'failed with unknown reason, exit code is: %s.'
                              % (assigner_id, target_wwpns, target_lun,
                                 exit_code))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=8,
                                                        userid=assigner_id,
                                                        msg=errmsg)
        LOG.info("Configuration of volume (WWPN:%s, LUN:%s) on the "
                 "target machine %s with FCP devices "
                 "%s is done." % (target_wwpns, target_lun, assigner_id,
                                  fcp_list))

    def config_detach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point, connections):
        LOG.info("Begin to deconfigure volume (WWPN:%s, LUN:%s) on the "
                 "target machine %s with FCP devices "
                 "%s." % (target_wwpns, target_lun, assigner_id, fcp_list))
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        self.configure_volume_detach(fcp_list, assigner_id, target_wwpns,
                                     target_lun, multipath, os_version,
                                     mount_point, linuxdist, connections)
        iucv_is_ready = self.check_IUCV_is_ready(assigner_id)
        if iucv_is_ready:
            # active mode should restart zvmguestconfigure to run reader file
            active_cmds = linuxdist.create_active_net_interf_cmd()
            ret = self._smtclient.execute_cmd_direct(
                assigner_id, active_cmds,
                timeout=CONF.volume.punch_script_execution_timeout)
            LOG.debug('detach scripts return values: %s' % ret)
            if ret['rc'] != 0:
                # if return code is 64 means timeout
                # no need to check the exist code of systemctl and return
                if ret['rc'] == 64:
                    errmsg = ('detach script execution in the target machine '
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
                if exit_code == 1:
                    errmsg = ('detach scripts execution failed because the '
                              'device %s in the target virtual machine %s '
                              'is in use.' % (fcp_list, assigner_id))
                else:
                    errmsg = ('detach scripts execution on fcp %s in the '
                              'target virtual machine %s failed '
                              'with unknow reason, exit code is: %s'
                              % (fcp_list, assigner_id, exit_code))
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=9,
                                                        userid=assigner_id,
                                                        msg=errmsg)
        LOG.info("Deconfiguration of volume (WWPN:%s, LUN:%s) on the "
                 "target machine %s with FCP devices "
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
        """Sync FCP DB with FCP list and ZVM"""
        # Note(CaoBiao): because we use FCP template to organize fcp devices
        # so no need to call _sync_db_with_fcp_list
        # First, sync with FCP list
        # self._sync_db_with_fcp_list()
        # Second, sync with ZVM
        self._sync_db_with_zvm()

    @staticmethod
    def _expand_fcp_list(fcp_list):
        """Expand fcp list string into a python list object which contains
        each fcp devices in the list string. A fcp list is composed of fcp
        device addresses, range indicator '-', and split indicator ';'.

        Example 1:
        if fcp_list is "0011-0013;0015;0017-0018",
        then the function will return
        {
          0: {'0011' ,'0012', '0013'}
          1: {'0015'}
          2: {'0017', '0018'}
        }

        Example 2:
        if fcp_list is empty string: '',
        then the function will return an empty set: {}

        ATTENTION: To support multipath, we expect fcp_list should be like
        "0011-0014;0021-0024", "0011-0014" should have been on same physical
        WWPN which we called path0, "0021-0024" should be on another physical
        WWPN we called path1 which is different from "0011-0014".
        path0 and path1 should have same count of FCP devices in their group.
        When attach, we will choose one WWPN from path0 group, and choose
        another one from path1 group. Then we will attach this pair of WWPNs
        together to the guest as a way to implement multipath.
        """
        LOG.debug("Expand FCP list %s" % fcp_list)

        if not fcp_list:
            return dict()
        fcp_list = fcp_list.strip()
        fcp_list = fcp_list.replace(' ', '')
        range_pattern = '[0-9a-fA-F]{1,4}(-[0-9a-fA-F]{1,4})?'
        match_pattern = "^(%(range)s)(;%(range)s;?)*$" % \
                        {'range': range_pattern}

        item_pattern = "(%(range)s)(,%(range)s?)*" % \
                       {'range': range_pattern}

        multi_match_pattern = "^(%(range)s)(;%(range)s;?)*$" % \
                       {'range': item_pattern}

        if not re.match(match_pattern, fcp_list) and \
           not re.match(multi_match_pattern, fcp_list):
            errmsg = ("Invalid FCP address %s") % fcp_list
            raise exception.SDKInternalError(msg=errmsg)

        fcp_devices = {}
        path_no = 0
        for _range in fcp_list.split(';'):
            for item in _range.split(','):
                # remove duplicate entries
                devices = set()
                if item != '':
                    if '-' not in item:
                        # single device
                        fcp_addr = int(item, 16)
                        devices.add("%04x" % fcp_addr)
                    else:
                        # a range of address
                        (_min, _max) = item.split('-')
                        _min = int(_min, 16)
                        _max = int(_max, 16)
                        for fcp_addr in range(_min, _max + 1):
                            devices.add("%04x" % fcp_addr)
                    if fcp_devices.get(path_no):
                        fcp_devices[path_no].update(devices)
                    else:
                        fcp_devices[path_no] = devices
            path_no = path_no + 1
        return fcp_devices

    def _shrink_fcp_list(self, fcp_list):
        """ Transform a FCP list to a string.

            :param fcp_list: (list) a list object contains FCPs.
            Case 1: only one FCP in the list.
                e.g. fcp_list = ['1A01']
            Case 2: all the FCPs are continuous.
                e.g. fcp_list =['1A01', '1A02', '1A03']
            Case 3: not all the FCPs are continuous.
                e.g. fcp_list = ['1A01', '1A02', '1A03',
                                '1A05',
                                '1AFF', '1B00', '1B01',
                                '1B04']
            Case 4: an empty list.
                e.g. fcp_list = []

            :return fcp_str: (str)
            Case 1: fcp_str = '1A01'
            Case 2: fcp_str = '1A01 - 1A03'
            Case 3: fcp_str = '1A01 - 1A03, 1A05,
                               1AFF - 1B01, 1B04'
            Case 4: fcp_str = ''
        """

        def __transform_fcp_list_into_str(local_fcp_list):
            """ Transform the FCP list into a string
                by recursively do the transformation
                against the first continuous range of the list,
                which is being shortened by list.pop(0) on the fly

                :param local_fcp_list:
                (list) a list object contains FCPs.

                In Python, hex is stored in the form of strings.
                Because incrementing is done on integers,
                we need to convert hex to an integer for doing math.
            """
            # Case 1: only one FCP in the list.
            if len(local_fcp_list) == 1:
                fcp_section.append(local_fcp_list[0])
            else:
                start_fcp = int(local_fcp_list[0], 16)
                end_fcp = int(local_fcp_list[-1], 16)
                count = len(local_fcp_list) - 1
                # Case 2: all the FCPs are continuous.
                if start_fcp + count == end_fcp:
                    # e.g. hex(int('1A01',16)) is '0x1a01'
                    section_str = '{} - {}'.format(
                        hex(start_fcp)[2:], hex(end_fcp)[2:])
                    fcp_section.append(section_str)
                # Case 3: not all the FCPs are continuous.
                else:
                    start_fcp = int(local_fcp_list.pop(0), 16)
                    for idx, fcp in enumerate(local_fcp_list.copy()):
                        next_fcp = int(fcp, 16)
                        # pop the fcp if it is continuous with the last
                        # e.g.
                        # when start_fcp is '1A01',
                        # pop '1A02' and '1A03'
                        if start_fcp + idx + 1 == next_fcp:
                            local_fcp_list.pop(0)
                            continue
                        # e.g.
                        # when start_fcp is '1A01',
                        # next_fcp '1A05' is NOT continuous with the last
                        else:
                            end_fcp = start_fcp + idx
                            # e.g.
                            # when start_fcp is '1A01',
                            # end_fcp is '1A03'
                            if start_fcp != end_fcp:
                                # e.g. hex(int('1A01',16)) is '0x1a01'
                                section_str = '{} - {}'.format(
                                    hex(start_fcp)[2:], hex(end_fcp)[2:])
                            # e.g.
                            # when start_fcp is '1A05',
                            # end_fcp is '1A05'
                            else:
                                section_str = hex(start_fcp)[2:]
                            fcp_section.append(section_str)
                            break
                    # recursively transform if FCP list still not empty
                    if local_fcp_list:
                        __transform_fcp_list_into_str(local_fcp_list)

        fcp_section = list()
        fcp_str = ''
        if fcp_list:
            # Verify each FCP is in hex format
            self._verify_fcp_list_in_hex_format(fcp_list)
            # sort fcp_list in hex order, e.g.
            # before sort: ['1E01', '1A02', '1D03']
            # after sort:  ['1A02', '1D03', '1E01']
            fcp_list.sort()
            __transform_fcp_list_into_str(fcp_list)
            # return a string contains all FCP
            fcp_str = ', '.join(fcp_section).upper()
        return fcp_str

    @staticmethod
    def _verify_fcp_list_in_hex_format(fcp_list):
        """Verify each FCP in the list is in Hex format
        :param fcp_list: (list) a list object contains FCPs.
        """
        if not isinstance(fcp_list, list):
            errmsg = ('fcp_list ({}) is not a list object.'
                      '').format(fcp_list)
            raise exception.SDKInvalidInputFormat(msg=errmsg)
        # Verify each FCP should be a 4-digit hex
        for fcp in fcp_list:
            if not (len(fcp) == 4 and
                    all(char in string.hexdigits for char in fcp)):
                errmsg = ('FCP list {} contains non-hex value.'
                          '').format(fcp_list)
                raise exception.SDKInvalidInputFormat(msg=errmsg)

    def _get_all_fcp_info(self, assigner_id, status=None):
        fcp_info = self._smtclient.get_fcp_info_by_status(assigner_id, status)

        return fcp_info

    def increase_fcp_usage(self, fcp, assigner_id=None):
        """Incrase fcp usage of given fcp

        Returns True if it's a new fcp, otherwise return False
        """
        # TODO: check assigner_id to make sure on the correct fcp record
        connections = self.db.get_connections_from_fcp(fcp)
        new = False
        if not connections:
            self.db.assign(fcp, assigner_id)
            new = True
        else:
            self.db.increase_usage(fcp)

        return new

    def add_fcp_for_assigner(self, fcp, assigner_id=None):
        """Incrase fcp usage of given fcp
        Returns True if it's a new fcp, otherwise return False
        """
        # get the sum of connections belong to assigner_id
        connections = self.db.get_connections_from_fcp(fcp)
        new = False
        if connections == 0:
            # ATTENTION: logically, only new fcp was added
            self.db.assign(fcp, assigner_id)
            new = True
        else:
            self.db.increase_usage_by_assigner(fcp, assigner_id)

        return new

    def decrease_fcp_usage(self, fcp, assigner_id=None):
        # TODO: check assigner_id to make sure on the correct fcp record
        connections = self.db.decrease_usage(fcp)

        return connections

    def _valid_fcp_devcie_wwpn(self, fcp_list, assigner_id):
        """This method is to check if the FCP wwpn_npiv or wwpn_phy is NULL, if yes, raise error"""
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

    def reserve_fcp_devices(self, assigner_id, fcp_template_id):
        """
        Reserve FCP devices by assigner_id and fcp_template_id. In this method:
        1. Get FCP list from db by assigner and fcp_template whose reserve=1
        2. If fcp_list is not empty, just to use them.
        3. If fcp_list is empty, get one from each path, then update 'reserved' and 'tmpl_id' in fcp table.

        Returns: The fcp list data structure: [(fcp_id, wwpn_npiv, wwpn_phy)].
                An example of fcp_list:
                [('1c10', 'c12345abcdefg1', 'c1234abcd33002641'),
                ('1d10', 'c12345abcdefg2', 'c1234abcd33002641')]
        """
        try:
            global _LOCK_RESERVE_FCP
            _LOCK_RESERVE_FCP.acquire()
            if fcp_template_id is None or len(fcp_template_id) == 0:
                errmsg = "No FCP template is specified and no default FCP template is found."
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)
            # go here, means try to attach volumes
            # first check whether this userid already has a FCP device
            # get the FCP devices belongs to assigner_id
            fcp_list = self.db.get_allocated_fcps_from_assigner(assigner_id, fcp_template_id)
            LOG.info("Previously allocated records %s for instance %s in fcp template %s." %
                     (fcp_list, assigner_id, fcp_template_id))
            if not fcp_list:
                # Sync DB to update FCP state,
                # so that allocating new FCPs is based on the latest FCP state
                self._sync_db_with_zvm()
                # allocate new ones if fcp_list is empty
                LOG.info("There is no allocated fcps for %s, will allocate "
                         "new ones." % assigner_id)
                if CONF.volume.get_fcp_pair_with_same_index:
                    '''
                    If use get_fcp_pair_with_same_index,
                    then fcp pair is randomly selected from below combinations.
                    [fa00,fb00],[fa01,fb01],[fa02,fb02]
                    '''
                    free_unreserved = self.db.get_fcp_devices_with_same_index(fcp_template_id)
                else:
                    '''
                    If use get_fcp_pair,
                    then fcp pair is randomly selected from below combinations.
                    [fa00,fb00],[fa01,fb00],[fa02,fb00]
                    [fa00,fb01],[fa01,fb01],[fa02,fb01]
                    [fa00,fb02],[fa01,fb02],[fa02,fb02]
                    '''
                    free_unreserved = self.db.get_fcp_devices(fcp_template_id)
                if not free_unreserved:
                    return []
                available_list = free_unreserved
                fcp_ids = [fcp[0] for fcp in free_unreserved]
                # record the assigner id in the fcp DB so that
                # when the vm provision with both root and data volumes
                # the root and data volume would get the same FCP devices
                # with the get_volume_connector call.
                assigner_id = assigner_id.upper()
                self.db.reserve_fcps(fcp_ids, assigner_id, fcp_template_id)
                LOG.info("Newly allocated %s fcp for %s assigner and FCP template %s" %
                         (fcp_ids, assigner_id, fcp_template_id))
            else:
                # reuse the old ones if fcp_list is not empty
                LOG.info("Found allocated fcps %s for %s in FCP template %s, will reuse them."
                         % (fcp_list, assigner_id, fcp_template_id))
                path_count = self.db.get_path_count(fcp_template_id)
                if len(fcp_list) != path_count:
                    # TODO: handle the case when len(fcp_list) < multipath_count
                    LOG.warning("FCPs previously assigned to %s includes %s, "
                                "it is not equal to the path count: %s." %
                                (assigner_id, fcp_list, path_count))
                self._valid_fcp_devcie_wwpn(fcp_list, assigner_id)
                # we got it from db, let's reuse it
                available_list = fcp_list
            return available_list
        except Exception as err:
            msg = "Failed to reserve FCP devices for assigner %s by FCP template %s error: %s" % \
                  (assigner_id, fcp_template_id, err)
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=11, msg=msg)
        finally:
            _LOCK_RESERVE_FCP.release()

    def unreserve_fcp_devices(self, assigner_id, fcp_template_id):
        """
            Unreserve FCP devices by assigner_id and fcp_template_id. In this method:
            1. Get FCP list from db by assigner and fcp_template whose reserved=1
            2. If fcp_list is not empty, choose the ones with connections=0, and then set reserved=0 in fcp table in db
            3. If fcp_list is empty, return empty list

            Returns: The fcp list data structure: [(fcp_id, wwpn_npiv, wwpn_phy, connections)].
                    An example of fcp_list:
                    [('1c10', 'c12345abcdefg1', 'c1234abcd33002641', 0),
                    ('1d10', 'c12345abcdefg2', 'c1234abcd33002641', 0)]
                    If no fcp can be gotten from db, return empty list.
        """
        try:
            # TODO check if the host only has one FCP template, if yes, use that one, or else, raise error.
            if fcp_template_id is None:
                errmsg = "fcp_template_id is not specified while releasing FCP devices."
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)
            fcp_list = self.db.get_reserved_fcps_from_assigner(assigner_id, fcp_template_id)
            if fcp_list:
                self._valid_fcp_devcie_wwpn(fcp_list, assigner_id)
                # the data structure of fcp_list is (fcp_id, wwpn_npiv, wwpn_phy, connections), only unreserve the fcps
                # with connections=0
                fcp_ids = [fcp[0] for fcp in fcp_list if fcp[3] == 0]
                LOG.info("Unreserve fcp device %s from "
                         "instance %s and FCP template %s." % (fcp_ids, assigner_id, fcp_template_id))
                self.db.unreserve_fcps(fcp_ids, fcp_template_id)
                return fcp_list
            return []
        except Exception as err:
            msg = "Failed to release FCP devices for assigner %s by FCP template %s.Error: %s" % \
                  (assigner_id, fcp_template_id, err)
            LOG.error(msg)
            raise exception.SDKGuestOperationError(rs=11, msg=msg)

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
            # this method is called by _sync_db_with_fcp_list
            # and _sync_db_with_zvm, change this msg to warning
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
        LOG.info("Enter: Update FCP dict into FCP table.")

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
        self.db.bulk_insert_zvm_fcp_info_into_fcp_table(fcp_info_need_insert)

        # Delete FCP records from FCP table
        # if it is connections=0 and reserve=0
        LOG.info("FCP devices exist in database but not in "
                 "z/VM any more: {}".format(del_fcp_set))
        fcp_ids_secure_to_delete = set()
        fcp_ids_not_found = set()
        for fcp in del_fcp_set:
            # example of a FCP record in fcp_dict_in_db
            # (fcp_id, userid, connections, reserved, wwpn_npiv,
            #  wwpn_phy, chpid, state, owner, tmpl_id)
            fcp_id, userid, connections, reserved, wwpn_npiv_db,\
                wwpn_phy_db, chpid_db, fcp_state_db, \
                    fcp_owner_db, tmpl_id = fcp_dict_in_db[fcp]
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
                     "FCPs: {}." .format(fcp_ids_not_found))

        # Update status for FCP records already existed in DB
        LOG.info("FCP devices exist in both database and "
                 "z/VM: {}".format(inter_set))
        fcp_ids_need_update = set()
        for fcp in inter_set:
            # example of a FCP record in fcp_dict_in_db
            # (fcp_id, userid, connections, reserved, wwpn_npiv,
            #  wwpn_phy, chpid, state, owner, tmpl_id)
            fcp_id, userid, connections, reserved, wwpn_npiv_db,\
                wwpn_phy_db, chpid_db, fcp_state_db, \
                    fcp_owner_db, tmpl_id = fcp_dict_in_db[fcp]
            # Check WWPNs changed or not
            wwpn_phy_zvm = fcp_dict_in_zvm[fcp].get_physical_port()
            wwpn_npiv_zvm = fcp_dict_in_zvm[fcp].get_npiv_port()
            # For an in-used FCP device,
            # if its npiv_wwpn_zvm is changed in zvm,
            # we will not update the npiv_wwpn_db in FCP DB;
            # because the npiv_wwpn_db is need when detaching volumes,
            # so as to delete the host-mapping from storage provider backend.
            # Hence, we use npiv_wwpn_db to override npiv_wwpn_zvm
            # in fcp_dict_in_zvm[fcp]
            if (wwpn_npiv_zvm != wwpn_npiv_db and
                    (0 != connections or 0 != reserved)):
                fcp_dict_in_zvm[fcp].set_npiv_port(wwpn_npiv_db)
            # Check chpid changed or not
            chpid_zvm = fcp_dict_in_zvm[fcp].get_chpid()
            # Check state changed or not
            # Possible state returned by ZVM:
            # 'active', 'free' or 'offline'
            fcp_state_zvm = fcp_dict_in_zvm[fcp].get_dev_status()
            # Check owner changed or not
            # Possbile FCP owner returned by ZVM:
            # VM userid: if the FCP is attached to a VM
            # A String "NONE": if the FCP is not attached
            fcp_owner_zvm = fcp_dict_in_zvm[fcp].get_owner()
            if wwpn_phy_db != wwpn_phy_zvm:
                fcp_ids_need_update.add(fcp)
            elif wwpn_npiv_db != wwpn_npiv_zvm:
                fcp_ids_need_update.add(fcp)
            elif chpid_db != chpid_zvm:
                fcp_ids_need_update.add(fcp)
            elif fcp_state_db != fcp_state_zvm:
                fcp_ids_need_update.add(fcp)
            elif fcp_owner_db != fcp_owner_zvm:
                fcp_ids_need_update.add(fcp)
            else:
                LOG.debug("No need to update record of FCP "
                          "device {}".format(fcp))
        fcp_info_need_update = [fcp_dict_in_zvm[fcp].to_tuple()
                                for fcp in fcp_ids_need_update]
        self.db.bulk_update_zvm_fcp_info_in_fcp_table(fcp_info_need_update)
        LOG.info("FCP devices need to update records in "
                 "fcp table {}".format(fcp_info_need_update))
        LOG.info("Exits: Update FCP dict into FCP table.")

    def _sync_db_with_zvm(self):
        """Sync FCP DB with the FCP info queried from zVM"""

        LOG.info("Enter: Sync FCP DB with FCP info queried from z/VM.")
        LOG.info("Querying FCP status on z/VM.")
        # Get a dict of all FCPs in ZVM
        fcp_dict_in_zvm = self.get_fcp_dict_in_zvm()
        # Update the dict of all FCPs into FCP table in database
        self.sync_fcp_table_with_zvm(fcp_dict_in_zvm)
        LOG.info("Exit: Sync FCP DB with FCP info queried from z/VM.")

    def create_fcp_template(self, name, description, fcp_devices,
                            host_default: bool = False,
                            default_sp_list: list = None):
        """Create a fcp template and return the basic information of
        the created template, for example:
        {
            'fcp_template': {
                'name': 'bjcb-test-template',
                'id': '36439338-db14-11ec-bb41-0201018b1dd2',
                'description': 'This is Default template',
                'host_default': True,
                'default_sp_list': ['sp4', 'v7k60']
            }
        }
        """
        LOG.info("Try to create a FCP template with name:%s,"
                 "description:%s and fcp devices: %s." % (name, description,
                                                          fcp_devices))
        # Generate a template id for this new template
        tmpl_id = str(uuid.uuid1())
        # Get fcp devices info index by path
        fcp_devices_by_path = self._expand_fcp_list(fcp_devices)
        # Insert related records in FCP database
        self.db.create_fcp_template(tmpl_id, name, description,
                                    fcp_devices_by_path, host_default,
                                    default_sp_list)
        # Return template basic info
        LOG.info("A FCP template was created with ID %s." % tmpl_id)
        return {'fcp_template': {'name': name,
                                 'id': tmpl_id,
                                 'description': description,
                                 'host_default': host_default,
                                 'default_sp_list': default_sp_list}}

    def _update_template_fcp_raw_usage(self, raw_usage, raw_item):
        """group raw_item with template_id and path
        raw_item format:
        [(fcp_id|tmpl_id|path|assigner_id|connections|reserved|
        wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id)]
        return format:
        {
            template_id: {
                path1: [(fcp_id, template_id, assigner_id, connections,
                         reserved, wwpn_npiv, wwpn_phy, chpid, state, owner,
                         tmpl_id),()],
                path2: [(),()],
            }
        }
        """
        fcp_id, template_id, path_id, assigner_id, connections,\
            reserved, wwpn_npiv, wwpn_phy, chpid, state, owner, tmpl_id = raw_item
        if not raw_usage.get(template_id, None):
            raw_usage[template_id] = {}
        if not raw_usage[template_id].get(path_id, None):
            raw_usage[template_id][path_id] = []
        # remove path_id from raw data, keep the last templ_id to
        # represent from which template this FCP has been allocated out.
        return_raw = (fcp_id, template_id, assigner_id, connections,
            reserved, wwpn_npiv, wwpn_phy, chpid, state, owner, tmpl_id)
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
                "is_default": is_default,
                "sp_name": [sp_name]
            }
        }
        """
        template_dict = {}
        for item in raw_data:
            id, name, description, is_default, sp_name = item
            if not template_dict.get(id, None):
                template_dict[id] = {"id": id,
                                     "name": name,
                                     "description": description,
                                     "is_default": is_default,
                                     "sp_name": [sp_name]}
            # one fcp template can be multiple sp's default template
            if sp_name and sp_name not in template_dict[id]["sp_name"]:
                template_dict[id]["sp_name"].append(sp_name)
        return template_dict

    def _update_template_fcp_statistics_usage(self, statistics_usage,
                                              raw_item):
        """Tranform raw usage in FCP database into statistic data.

        :param statistics_usage: (dict) to store statistics info
        :param raw_item: [list] to represent db query result

        raw_item format:

        [(fcp_id|tmpl_id|path|assigner_id|connections|reserved|
        wwpn_npiv|wwpn_phy|chpid|state|owner|tmpl_id)]

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
        fcp_id, template_id, path_id, assigner_id, connections,\
            reserved, _, _, chpid, state, owner, _ = raw_item

        # The raw_item is for each fcp device, so there are multiple
        # items for each single fcp template. 
        # But the return result needs to group all the items by fcp template,
        # so construct a dict statistics_usage[template_id]
        # with template_id as key to group the info.
        # template_id key also will be used to join with template base info
        if not statistics_usage.get(template_id, None):
            statistics_usage[template_id] = {}
        if not statistics_usage[template_id].get(path_id, None):
            statistics_usage[template_id][path_id] = {
                "total": [],
                "available": [],
                "allocated": [],
                "reserve_only": [],
                "connection_only": [],
                "unallocated_but_active": [],
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
                LOG.warning("When getting statistics, found a FCP "
                            "%s in fcp template %s, but not found in "
                            "z/VM." % (str(fcp_id), str(template_id)))
            # case H: (state = offline)
            # this FCP in database but offline in z/VM
            if state == "offline":
                statistics_usage[template_id][path_id]["offline"].append(
                    fcp_id)
                LOG.warning("When getting statistics, found state of FCP "
                            "record %s is offline in database." % str(fcp_id))
            # found this FCP in z/VM
            if connections == 0:
                if reserved == 0:
                    # case A: (reserve=0 and conn=0 and state=free)
                    # this FCP is available for use
                    if state == "free":
                        statistics_usage[
                            template_id][path_id]["available"].append(fcp_id)
                        LOG.debug("When getting statistics, found "
                                  "an available FCP record %s in "
                                  "database." % str(fcp_id))
                    # case E: (conn=0 and reserve=0 and state=active)
                    # this FCP is available in database but its state
                    # is active in smcli output
                    if state == "active":
                        statistics_usage[
                            template_id][path_id]["unallocated_but_active"].\
                            append((fcp_id, owner))
                        LOG.warning("When getting statistics, found a FCP "
                                    "record %s available in database but its "
                                    "state is active, it may be occupied by "
                                    "a userid outside of this ZCC." % str(
                                    fcp_id))
                else:
                    # case C: (reserve=1 and conn=0)
                    # the fcp should be in task or a bug happen
                    statistics_usage[
                        template_id][path_id]["reserve_only"].append(fcp_id)
                    LOG.warning("When getting statistics, found a FCP "
                                "record %s reserve_only." % str(fcp_id))
            else:
                # connections != 0
                if reserved == 0:
                    # case D: (reserve = 0 and conn != 0)
                    # must have a bug result in this
                    statistics_usage[template_id][
                        path_id]["connection_only"].append(fcp_id)
                    LOG.warning("When getting statistics, found a FCP "
                                "record %s unreserved in database but "
                                "its connections is not 0." % str(fcp_id))
                else:
                    # case B: (reserve=1 and conn!=0)
                    # ZCC allocated this to a userid
                    statistics_usage[
                        template_id][path_id]["allocated"].append(fcp_id)
                    LOG.debug("When getting statistics, found an allocated "
                            "FCP record: %s." % str(fcp_id))
                # case F: (conn!=0 and state=free)
                if state == "free":
                    statistics_usage[template_id][
                        path_id]["allocated_but_free"].append(fcp_id)
                    LOG.warning("When getting statistics, found a FCP "
                                "record %s allocated by ZCC but its state is "
                                "free." % str(fcp_id))
                # case I: ((conn != 0) & assigner_id != owner)
                elif assigner_id != owner and state != "notfound":
                    LOG.warning("When getting statistics, found a FCP "
                                "record %s allocated by ZCC but its assigner "
                                "differs from owner." % str(fcp_id))
            if chpid:
                if not statistics_usage[
                    template_id][path_id]["CHPIDs"].get(chpid, None):
                    statistics_usage[
                        template_id][path_id]["CHPIDs"] = {chpid: []}
                statistics_usage[
                    template_id][path_id]["CHPIDs"][chpid].append(fcp_id)
        # this FCP in template_fcp_mapping table but not found in z/VM
        else:
            # add into 'total' and 'not_found'
            statistics_usage[template_id][path_id]["total"].append(fcp_id)
            statistics_usage[template_id][path_id]["notfound"].append(fcp_id)
            LOG.warning("When getting statistics, found a FCP "
                        "%s in fcp template %s, but not found in "
                        "z/VM." % (str(fcp_id), str(template_id)))
        return statistics_usage

    def _shrink_fcp_list_in_statistics_usage(self, statistics_usage):
        for template_statistics in statistics_usage.values():
            for path in template_statistics:
                # section is one from
                # 'allocated', 'available', 'notfound', 'offline'
                # 'allocated_but_free', 'unallocated_but_active'
                for section in template_statistics[path]:
                    # Do NOT transform unallocated_but_active,
                    # because its value also contains VM userid.
                    # e.g. [('1b04','owner1'), ('1b05','owner2')]
                    if (section != 'unallocated_but_active' and
                        section != 'CHPIDs'):
                        fcp_list = template_statistics[path][section]
                        template_statistics[path][section] = (
                            self._shrink_fcp_list(fcp_list))
                    if section == 'CHPIDs':
                        for chpid, fcps in template_statistics[
                            path]['CHPIDs'].items():
                            fcp_list = fcps
                            template_statistics[path]['CHPIDs'][chpid] = (
                                self._shrink_fcp_list(fcp_list))

    def get_fcp_templates(self, template_id_list=None, assigner_id=None,
                          default_sp_list=None, host_default=False):
        """Get template base info by template_id_list or filters
        :param template_id_list: (list) a list of template id,
        if it is None, get fcp templates with other parameter
        :param assigner_id: (str) a string of VM userid
        :param default_sp_list: (list) a list of storage provider or 'all',
        to get storage provider's default fcp templates

        when sp_host_list = ['all'], will get all storage providers' default
        fcp templates. For example, there are 3 fcp templates are set as
        storage providers' default template, then all these 3 fcp templates
        will return as below:
        {
            "fcp_templates": [
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd2",
                "name": "default_template",
                "description": "This is Default template",
                "is_default": 1,
                "sp_name": [
                    "v7k60",
                    "sp4"
                ]
                },
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd3",
                "name": "test_template",
                "description": "just for test",
                "is_default": 0,
                "sp_name": [
                    "ds8k60c1"
                ]
                },
                {
                "id": "12345678",
                "name": "templatet1",
                "description": "test1",
                "is_default": 0,
                "sp_name": [
                    "sp3"
                ]
                }
            ]
        }

        when sp_host_list is a storage provider name list, will return these
        providers' default fcp templates.

        Example:
        sp_host_list = ['v7k60', 'ds8k60c1]

        return:
        {
            "fcp_templates": [
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd2",
                "name": "default_template",
                "description": "This is Default template",
                "is_default": 1,
                "sp_name": [
                    "v7k60",
                    "sp4"
                ]
                },
                {
                "id": "36439338-db14-11ec-bb41-0201018b1dd3",
                "name": "test_template",
                "description": "just for test",
                "is_default": 0,
                "sp_name": [
                    "ds8k60c1"
                ]
                }
            ]
        }
        :param host_default: (boolean) whether or not get host default fcp
        template
        :return: (dict) the base info of template
        """
        raw = []
        ret = []

        if template_id_list:
            raw = self.db.get_fcp_templates(template_id_list)
        
        elif assigner_id:
            raw = self.db.get_fcp_template_by_assigner_id(assigner_id)

        elif default_sp_list:
            raw = self.db.get_sp_default_fcp_template(default_sp_list)
        
        elif host_default:
            raw = self.db.get_host_default_fcp_template()
        
        else:
            # if no parameter, will get all fcp templates
            raw = self.db.get_fcp_templates(template_id_list)

        template_list = self.extract_template_info_from_raw_data(raw)

        for value in template_list.values():
            ret.append(value)
        return {"fcp_templates": ret}

    def get_fcp_templates_details(self, template_id_list=None, raw=False,
                                  statistics=True, sync_with_zvm=False):
        """Get fcp templates detail info.
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
                    "is_default":1,
                    "sp_name":[
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
                        'unallocated_but_active': [('1B04','owner1'),
                                                ('1B05','owner2')]
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
                            "unallocated_but_active":[

                            ],
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
                            "unallocated_but_active":[

                            ],
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
        #         "sp_name": [sp_name]
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
            #         "sp_name": [sp_name],
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
                # only the fcp template which has fcp in zvm has
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
            #         "is_default": is_default,
            #         "sp_name": [sp_name],
            #          "statistics": {
            #              path1: {},
            #              path2: {}}
            #          }
            #   }
            # }
        for value in template_info.values():
            ret.append(value)
        return {"fcp_templates": ret}


# volume manager for FCP protocol
class FCPVolumeManager(object):
    def __init__(self):
        self.fcp_mgr = FCPManager()
        self.config_api = VolumeConfiguratorAPI()
        self._smtclient = smtclient.get_smtclient()
        self._lock = threading.RLock()
        self.db = database.FCPDbOperator()

    def _dedicate_fcp(self, fcp, assigner_id):
        self._smtclient.dedicate_device(assigner_id, fcp, fcp, 0)

    def _add_disks(self, fcp_list, assigner_id, target_wwpns, target_lun,
                   multipath, os_version, mount_point,):
        self.config_api.config_attach(fcp_list, assigner_id, target_wwpns,
                                      target_lun, multipath, os_version,
                                      mount_point)

    def _rollback_dedicated_fcp(self, fcp_list, assigner_id,
                                all_fcp_list=None):
        # fcp param should be a list
        for fcp in fcp_list:
            with zvmutils.ignore_errors():
                LOG.info("Rolling back dedicated FCP: %s" % fcp)
                connections = self.fcp_mgr.decrease_fcp_usage(
                    fcp, assigner_id)
                if connections == 0:
                    self._undedicate_fcp(fcp, assigner_id)
        # If attach volume fails, we need to unreserve all FCP devices.
        if all_fcp_list:
            for fcp in all_fcp_list:
                if not self.db.get_connections_from_fcp(fcp):
                    LOG.info("Unreserve the fcp device %s", fcp)
                    self.db.unreserve(fcp)

    def _attach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                multipath, os_version, mount_point, path_count,
                is_root_volume):
        """Attach a volume

        First, we need translate fcp into local wwpn, then
        dedicate fcp to the user if it's needed, after that
        call smt layer to call linux command
        """
        LOG.info("Start to attach volume to FCP devices "
                 "%s on machine %s." % (fcp_list, assigner_id))

        # fcp_status is like { '1a10': 'True', '1b10', 'False' }
        # True or False means it is first attached or not
        # We use this bool value to determine dedicate or not
        fcp_status = {}
        for fcp in fcp_list:
            fcp_status[fcp] = self.fcp_mgr.add_fcp_for_assigner(fcp,
                                                                assigner_id)
        if is_root_volume:
            LOG.info("Is root volume, adding FCP records %s to %s is "
                     "done." % (fcp_list, assigner_id))
            # FCP devices for root volume will be defined in user directory
            return []

        LOG.debug("The status of fcp devices before "
                  "dedicating them to %s is: %s." % (assigner_id, fcp_status))

        try:
            # dedicate the new FCP devices to the userid
            for fcp in fcp_list:
                if fcp_status[fcp]:
                    # only dedicate the ones first attached
                    LOG.info("Start to dedicate FCP %s to "
                             "%s." % (fcp, assigner_id))
                    self._dedicate_fcp(fcp, assigner_id)
                    LOG.info("FCP %s dedicated to %s is "
                             "done." % (fcp, assigner_id))
                else:
                    LOG.info("This is not the first volume for FCP %s, "
                             "skip dedicating FCP device." % fcp)
            # online and configure volumes in target userid
            self._add_disks(fcp_list, assigner_id, target_wwpns,
                            target_lun, multipath, os_version,
                            mount_point)
        except exception.SDKBaseException as err:
            errmsg = ("Attach volume failed with "
                      "error:" + err.format_message())
            LOG.error(errmsg)
            self._rollback_dedicated_fcp(fcp_list, assigner_id,
                                         all_fcp_list=fcp_list)
            raise exception.SDKBaseException(msg=errmsg)
        LOG.info("Attaching volume to FCP devices %s on machine %s is "
                 "done." % (fcp_list, assigner_id))

    def volume_refresh_bootmap(self, fcpchannels, wwpns, lun,
                               wwid='',
                               transportfiles=None, guest_networks=None):
        ret = None
        with zvmutils.acquire_lock(self._lock):
            LOG.debug('Enter lock scope of volume_refresh_bootmap.')
            ret = self._smtclient.volume_refresh_bootmap(fcpchannels, wwpns,
                                        lun, wwid=wwid,
                                        transportfiles=transportfiles,
                                        guest_networks=guest_networks)
        LOG.debug('Exit lock of volume_refresh_bootmap with ret %s.' % ret)
        return ret

    def attach(self, connection_info):
        """Attach a volume to a guest

        connection_info contains info from host and storage side
        this mostly includes
        host side FCP: this can get host side wwpn
        storage side wwpn
        storage side lun

        all the above assume the storage side info is given by caller
        """
        fcp = connection_info['zvm_fcp']
        wwpns = connection_info['target_wwpn']
        target_lun = connection_info['target_lun']
        assigner_id = connection_info['assigner_id']
        assigner_id = assigner_id.upper()
        multipath = connection_info['multipath']
        multipath = multipath.lower()
        if multipath == 'true':
            multipath = True
        else:
            multipath = False
        os_version = connection_info['os_version']
        mount_point = connection_info['mount_point']
        is_root_volume = connection_info.get('is_root_volume', False)

        # TODO: check exist in db?
        if is_root_volume is False and \
                not zvmutils.check_userid_exist(assigner_id):
            LOG.error("User directory '%s' does not exist." % assigner_id)
            raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % assigner_id), modID='volume')
        else:
            # TODO: the length of fcp is the count of paths in multipath
            path_count = len(fcp)
            # transfer to lower cases
            fcp_list = [x.lower() for x in fcp]
            target_wwpns = [wwpn.lower() for wwpn in wwpns]
            self._attach(fcp_list, assigner_id,
                         target_wwpns, target_lun,
                         multipath, os_version,
                         mount_point, path_count,
                         is_root_volume)

    def _undedicate_fcp(self, fcp, assigner_id):
        self._smtclient.undedicate_device(assigner_id, fcp)

    def _remove_disks(self, fcp_list, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point, connections):
        self.config_api.config_detach(fcp_list, assigner_id, target_wwpns,
                                      target_lun, multipath, os_version,
                                      mount_point, connections)

    def _detach(self, fcp_list, assigner_id, target_wwpns, target_lun,
                multipath, os_version, mount_point, is_root_volume,
                update_connections_only):
        """Detach a volume from a guest"""
        LOG.info("Start to detach volume on machine %s from "
                 "FCP devices %s" % (assigner_id, fcp_list))
        # fcp_connections is like {'1a10': 0, '1b10': 3}
        # the values are the connections colume value in database
        fcp_connections = {}
        # need_rollback is like {'1a10': False, '1b10': True}
        # if need_rollback set to True, we need rollback
        # when some actions failed
        need_rollback = {}
        for fcp in fcp_list:
            # need_rollback default to True
            need_rollback[fcp] = True
            try:
                connections = self.fcp_mgr.decrease_fcp_usage(fcp, assigner_id)
            except exception.SDKObjectNotExistError:
                connections = 0
                # if the connections already are 0 before decreasing it,
                # there might be something wrong, no need to rollback
                # because rollback increase connections and the FCPs
                # are not available anymore
                need_rollback[fcp] = False
                LOG.warning("The connections of FCP device %s is 0.", fcp)
            fcp_connections[fcp] = connections

        # If is root volume we only need update database record
        # because the dedicate is done by volume_refresh_bootmap
        # If update_connections set to True, means upper layer want
        # to update database record only. For example, try to delete
        # the instance, then no need to waste time on undedicate
        if is_root_volume or update_connections_only:
            if update_connections_only:
                LOG.info("Update connections only, deleting FCP records %s "
                         "from %s is done." % (fcp_list, assigner_id))
            else:
                LOG.info("Is root volume, deleting FCP records %s from %s is "
                         "done." % (fcp_list, assigner_id))
            return

        # when detaching volumes, if userid not exist, no need to
        # raise exception. we stop here after the database operations done.
        if not zvmutils.check_userid_exist(assigner_id):
            LOG.warning("Found %s not exist when trying to detach volumes "
                        "from it.", assigner_id)
            return

        try:
            self._remove_disks(fcp_list, assigner_id, target_wwpns, target_lun,
                               multipath, os_version, mount_point, connections)
            for fcp in fcp_list:
                if not fcp_connections.get(fcp, 0):
                    LOG.info("Start to undedicate FCP %s from "
                             "%s." % (fcp, assigner_id))
                    self._undedicate_fcp(fcp, assigner_id)
                    LOG.info("FCP %s undedicated from %s is "
                             "done." % (fcp, assigner_id))
                else:
                    LOG.info("Found still have volumes on FCP %s, "
                             "skip undedicating FCP device." % fcp)
        except (exception.SDKBaseException,
                exception.SDKSMTRequestFailed) as err:
            rc = err.results['rc']
            rs = err.results['rs']
            if rc == 404 or rc == 204 and rs == 8:
                # We ignore the already undedicate FCP device exception.
                LOG.warning("The FCP device %s has already undedicdated", fcp)
            else:
                errmsg = "detach failed with error:" + err.format_message()
                LOG.error(errmsg)
                for fcp in fcp_list:
                    if need_rollback.get(fcp, True):
                        # rollback the connections data before remove disks
                        LOG.info("Rollback usage of fcp %s on instance %s."
                                 % (fcp, assigner_id))
                        self.fcp_mgr.increase_fcp_usage(fcp, assigner_id)
                        _userid, _reserved, _conns = self.get_fcp_usage(fcp)
                        LOG.info("After rollback, fcp usage of %s "
                                 "is (assigner_id: %s, reserved:%s, "
                                 "connections: %s)."
                                 % (fcp, _userid, _reserved, _conns))
                with zvmutils.ignore_errors():
                    self._add_disks(fcp_list, assigner_id,
                                    target_wwpns, target_lun,
                                    multipath, os_version, mount_point)
                raise exception.SDKBaseException(msg=errmsg)
        LOG.info("Detaching volume on machine %s from FCP devices %s is "
                 "done." % (assigner_id, fcp_list))

    def detach(self, connection_info):
        """Detach a volume from a guest
        """
        fcp = connection_info['zvm_fcp']
        wwpns = connection_info['target_wwpn']
        target_lun = connection_info['target_lun']
        assigner_id = connection_info['assigner_id']
        assigner_id = assigner_id.upper()
        multipath = connection_info['multipath']
        os_version = connection_info['os_version']
        mount_point = connection_info['mount_point']
        multipath = multipath.lower()
        if multipath == 'true':
            multipath = True
        else:
            multipath = False

        is_root_volume = connection_info.get('is_root_volume', False)
        update_connections_only = connection_info.get(
                'update_connections_only', False)
        # transfer to lower cases
        fcp_list = [x.lower() for x in fcp]
        target_wwpns = [wwpn.lower() for wwpn in wwpns]
        self._detach(fcp_list, assigner_id,
                     target_wwpns, target_lun,
                     multipath, os_version, mount_point,
                     is_root_volume, update_connections_only)

    def get_volume_connector(self, assigner_id, reserve, fcp_template_id=None):
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
            'fcp_template_id': fcp_template_id # if user doesn't specify it, it is either the SP default or the host
                               default template id
        }
        """
        # TODO validate fcp_template_id
        fcp_tmpl_id = fcp_template_id if fcp_template_id else self.db.get_default_fcp_template()
        empty_connector = {'zvm_fcp': [], 'wwpns': [], 'host': '',
                           'phy_to_virt_initiators': {}, 'fcp_paths': 0, 'fcp_template_id': fcp_tmpl_id}

        # get lpar name of the userid, if no host name got, raise exception
        zvm_host = zvmutils.get_lpar_name()
        if zvm_host == '':
            errmsg = "failed to get z/VM LPAR name."
            LOG.error(errmsg)
            raise exception.SDKVolumeOperationError(rs=11,
                                                    userid=assigner_id,
                                                    msg=errmsg)
        """
            Reserve or unreserve FCP device according to assigner id and FCP template id.
            The data structure of fcp_list is:  [(fcp_id, wwpn_npiv, wwpn_phy, connections)].
            An example of fcp_list:
                [('1c10', 'c12345abcdefg1', 'c1234abcd33002641', 0),
                ('1d10', 'c12345abcdefg2', 'c1234abcd33002641', 0)]
        """
        if reserve:
            # The data structure of fcp_list is: [(fcp_id, wwpn_npiv, wwpn_phy)]
            fcp_list = self.fcp_mgr.reserve_fcp_devices(assigner_id, fcp_tmpl_id)
        else:
            # The data structure of fcp_list is: [(fcp_id, wwpn_npiv, wwpn_phy, connections)]
            fcp_list = self.fcp_mgr.unreserve_fcp_devices(assigner_id, fcp_template_id)
        if not fcp_list:
            errmsg = ("No available FCP device found for %s and FCP template %s." % (assigner_id, fcp_template_id))
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
                     'fcp_template_id': fcp_tmpl_id}
        LOG.info('get_volume_connector returns %s for assigner %s and fcp template %s' %
                 (connector, assigner_id, fcp_tmpl_id))
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
    
    def get_all_fcp_usage(self, assigner_id=None, raw=False, statistics=True,
                          sync_with_zvm=False):
        """Get all fcp information grouped by FCP id.
        :param assigner_id: (str) if is None, will get all fcps info in db.
        :param raw: (boolean) if is True, will get raw fcp usage data
        :param statistics: (boolean) if is True, will get statistics data
            of all FCPs
        :param sync_with_zvm: (boolean) if is True, will call SMCLI command
            to sync the FCP state in the database
        :return: (dict) the raw and/or statistic data of all FCP devices
        The return data example:
        Example 1:
        if FCP DB is empty and raw=True statistics=False assigner_id=None
        {
            "raw": {}
        }
        Example 2:
        if FCP DB is empty and raw=False statistics=True assigner_id=None
        {
            "statistics": {}
        }
        Example 3:
        if FCP DB is empty and raw=True statistics=True assigner_id=None
        {
            "raw": {}, "statistics": {}
        }
        Example 4:
        if FCP DB is NOT empty and raw=True statistics=True assigner_id=None
        {
            "raw": {
                  # (fcp_id, userid, connections, reserved, path,
                  #  comment, wwpn_npiv, wwpn_phy, chpid, tmpl_id),
                  0 : (
                    ('283c',  'user1', 2, 1, 0,
                     {'state': 'active','owner: 'ABCD0001'},
                     'c05076ddf7003bf4','c05076ddf7001181'),
                    ('183c',  '', 0, 0, 0, {'state': 'notfound'},
                     'c05076ddf7004321', 'c05076ddf7001181', 27, ''),
                  ),
                  1 : (
                    ('383c',  'user3', 0, 0, 1,
                     {'state': 'active', 'owner': 'ABCD0001'}),
                     'c05076ddf7001234', 'c05076ddf7001182'
                    ('483c',  'user2', 0, 0, 1,
                     {'state': 'free', 'owner': 'NONE'}),
                     'c05076ddf7004322', 'c05076ddf7001182', 27, ''
                  )
                  ...
            },
            "statistics": {
                0: {
                    # case A: (reserve = 0 and conn = 0 and state = free)
                    # FCP is available and in free status
                    "available": ('1A00','1A05',...)
                    # case B: (reserve = 1 and conn != 0)
                    # nomral in-use FCP
                    "allocated": ('1B00','1B05',...)
                    # case C: (reserve = 1, conn = 0)
                    # the fcp should be in task or a bug cause this situation
                    "reserve_only": ('1C00', '1C05', ...)
                    # case D: (reserve = 0 and conn != 0)
                    # should be a bug result in this situation
                    "connection_only": ('1C00', '1C05', ...)
                    # case E: (reserve = 0, conn = 0, state = active)
                    # FCP occupied out-of-band
                    'unallocated_but_active': [('1B04','owner1'),
                                               ('1B05','owner2')]
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
                },
                1: {
                    ...
                }
            }
        }
        """
        ret = {}
        # sync the state of FCP devices by calling smcli
        if sync_with_zvm:
            self.fcp_mgr._sync_db_with_zvm()
        # get raw query results from database
        try:
            raw_usage = self.db.get_all_fcps_of_assigner(assigner_id)
        except exception.SDKObjectNotExistError:
            LOG.warning("When getting fcp usage, no fcp records found in "
                        "database and ignore the exception.")
            raw_usage = []

        if assigner_id:
            statistics = False
            raw = True
            LOG.debug("Got all fcp usage of userid %s: "
                      "%s" % (assigner_id, raw_usage))
        else:
            # if userid is None, get usage of all the fcps
            LOG.debug("Got all fcp usage: %s" % raw_usage)

        # transfer records into dict grouped by path ID
        raw_usage_by_path = {}
        statistics_usage = {}
        for item in raw_usage:
            # get raw fcp usage
            if raw:
                self._update_template_fcp_raw_usage(raw_usage_by_path, item)
            # get fcp statistics usage
            if statistics:
                self._update_statistics_usage(statistics_usage, item)
        # store usage into returned value
        if raw:
            LOG.debug("raw FCP usage: %s" % raw_usage_by_path)
            ret["raw"] = raw_usage_by_path
        if statistics:
            LOG.info("statistic FCP usage before shrink: %s"
                     % statistics_usage)
            # Transform FCP format from list to str
            for path in statistics_usage:
                # section is one from
                # 'allocated', 'available', 'notfound', 'offline'
                # 'allocated_but_free', 'unallocated_but_active'
                for section in statistics_usage[path]:
                    # Do NOT transform unallocated_but_active,
                    # because its value also contains VM userid.
                    # e.g. [('1b04','owner1'), ('1b05','owner2')]
                    if section != 'unallocated_but_active':
                        fcp_list = statistics_usage[path][section]
                        statistics_usage[path][section] = (
                            self.fcp_mgr._shrink_fcp_list(fcp_list))
            ret["statistics"] = statistics_usage
            LOG.info("statistic FCP usage after shrink: %s"
                     % statistics_usage)
        return ret

    def get_fcp_usage(self, fcp):
        userid, reserved, connections = self.db.get_usage_of_fcp(fcp)
        LOG.debug("Got userid:%s, reserved:%s, connections:%s of "
                  "FCP:%s" % (userid, reserved, connections, fcp))
        return userid, reserved, connections

    def set_fcp_usage(self, fcp, assigner_id, reserved, connections):
        self.db.update_usage_of_fcp(fcp, assigner_id, reserved, connections)
        LOG.info("Set usage of fcp %s to userid:%s, reserved:%s, "
                 "connections:%s." % (fcp, assigner_id, reserved, connections))
