#    Copyright 2017,2021 IBM Corp.
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
                               transportfiles='', guest_networks=None):
        return self._volume_manager.volume_refresh_bootmap(fcpchannel, wwpn,
                                            lun, wwid=wwid,
                                            transportfiles=transportfiles,
                                            guest_networks=guest_networks)

    def get_volume_connector(self, assigner_id, reserve):
        return self._volume_manager.get_volume_connector(assigner_id, reserve)

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
            ret = self._smtclient.execute_cmd_direct(assigner_id, active_cmds)
            LOG.debug('attach scripts return values: %s' % ret)
            if ret['rc'] != 0:
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
            ret = self._smtclient.execute_cmd_direct(assigner_id, active_cmds)
            LOG.debug('detach scripts return values: %s' % ret)
            if ret['rc'] != 0:
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
    def _get_wwpn_from_line(info_line):
        wwpn = info_line.split(':')[-1].strip().lower()
        return wwpn if (wwpn and wwpn.upper() != 'NONE') else None

    @staticmethod
    def _get_dev_number_from_line(info_line):
        dev_no = info_line.split(':')[-1].strip().lower()
        return dev_no if dev_no else None

    @staticmethod
    def _get_dev_status_from_line(info_line):
        dev_status = info_line.split(':')[-1].strip().lower()
        return dev_status if dev_status else None

    @staticmethod
    def _get_chpid_from_line(info_line):
        chpid = info_line.split(':')[-1].strip().upper()
        return chpid if chpid else None

    @staticmethod
    def _get_owner_from_line(info_line):
        owner = info_line.split(':')[-1].strip().upper()
        return owner if owner else None

    def _parse(self, init_info):
        """Initialize a FCP device object from several lines of string
           describing properties of the FCP device.
           Here is a sample:
               opnstk1: FCP device number: B83D
               opnstk1:   Status: Free
               opnstk1:   NPIV world wide port number: NONE
               opnstk1:   Channel path ID: 59
               opnstk1:   Physical world wide port number: 20076D8500005181
           The format comes from the response of xCAT, do not support
           arbitrary format.
        """
        lines_per_item = constants.FCP_INFO_LINES_PER_ITEM
        if isinstance(init_info, list) and (len(init_info) == lines_per_item):
            self._dev_no = self._get_dev_number_from_line(init_info[0])
            self._dev_status = self._get_dev_status_from_line(init_info[1])
            self._npiv_port = self._get_wwpn_from_line(init_info[2])
            self._chpid = self._get_chpid_from_line(init_info[3])
            self._physical_port = self._get_wwpn_from_line(init_info[4])
            self._owner = self._get_owner_from_line(init_info[5])

    def get_dev_no(self):
        return self._dev_no

    def get_dev_status(self):
        return self._dev_status

    def get_npiv_port(self):
        return self._npiv_port

    def get_physical_port(self):
        return self._physical_port

    def get_chpid(self):
        return self._chpid

    def get_owner(self):
        return self._owner

    def is_valid(self):
        # FIXME: add validation later
        return True


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
        # First, sync with FCP list
        self._sync_db_with_fcp_list()
        # Second, sync with ZVM
        self._sync_db_with_zvm()

    @staticmethod
    def _expand_fcp_list(fcp_list):
        """Expand fcp list string into a python list object which contains
        each fcp devices in the list string. A fcp list is composed of fcp
        device addresses, range indicator '-', and split indicator ';'.

        For example,
        if fcp_list is "0011-0013;0015;0017-0018",
        then the function will return
        {
          0: {'0011' ,'0012', '0013'}
          1: {'0015'}
          2: {'0017', '0018'}
        }

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

    def _get_all_fcp_info(self, assigner_id, status=None):
        fcp_info = self._smtclient.get_fcp_info_by_status(assigner_id, status)

        return fcp_info

    def find_and_reserve_fcp(self, assigner_id):
        """reserve the fcp to assigner_id

        The function to reserve a fcp for user
        1. Check whether assigner_id has a fcp already
           if yes, make the reserve of that record to 1
        2. No fcp, then find a fcp and reserve it

        fcp will be returned, or None indicate no fcp
        """
        fcp_list = self.db.get_allocated_fcps_from_assigner(assigner_id)
        if not fcp_list:
            new_fcp = self.db.find_and_reserve()
            if new_fcp is None:
                LOG.info("no more fcp to be allocated")
                return None

            LOG.debug("allocated %s fcp for %s assigner" %
                      (new_fcp, assigner_id))
            return new_fcp
        else:
            # we got it from db, let's reuse it
            old_fcp = fcp_list[0][0]
            self.db.reserve(fcp_list[0][0])
            return old_fcp

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

    def unreserve_fcp(self, fcp, assigner_id=None):
        # TODO: check assigner_id to make sure on the correct fcp record
        self.db.unreserve(fcp)

    def is_reserved(self, fcp):
        self.db.is_reserved(fcp)

    def get_available_fcp(self, assigner_id, reserve):
        """ Return a group of available FCPs, one FCP per path
            For example,
            if there are 2 FCP paths,
            then return a group of 2 FCPs: [1A03, 1B03],
            where 1A03 is from one path
            while 1B03 if from the other path
        """
        available_list = []
        if not reserve:
            # go here, means try to detach volumes, cinder still need the info
            # of the FCPs belongs to assigner to do some cleanup jobs
            fcp_list = self.db.get_reserved_fcps_from_assigner(assigner_id)
            LOG.info("Got fcp records %s belonging to instance %s in "
                     "Unreserve mode." % (fcp_list, assigner_id))
            # in this case, we just return the fcp_list
            # no need to allocated new ones if fcp_list is empty
            for old_fcp in fcp_list:
                available_list.append(old_fcp[0])
            return available_list

        # go here, means try to attach volumes
        # first check whether this userid already has a FCP device
        # get the FCP devices belongs to assigner_id
        fcp_list = self.db.get_allocated_fcps_from_assigner(assigner_id)
        LOG.info("Previously allocated records %s for instance %s." %
                 (fcp_list, assigner_id))
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
                free_unreserved = self.db.get_fcp_pair_with_same_index()
            else:
                '''
                If use get_fcp_pair,
                then fcp pair is randomly selected from below combinations.
                [fa00,fb00],[fa01,fb00],[fa02,fb00]
                [fa00,fb01],[fa01,fb01],[fa02,fb01]
                [fa00,fb02],[fa01,fb02],[fa02,fb02]
                '''
                free_unreserved = self.db.get_fcp_pair()
            for item in free_unreserved:
                available_list.append(item)
                # record the assigner id in the fcp DB so that
                # when the vm provision with both root and data volumes
                # the root and data volume would get the same FCP devices
                # with the get_volume_connector call.
                assigner_id = assigner_id.upper()
                self.db.assign(item, assigner_id, update_connections=False)

            LOG.info("Newly allocated %s fcp for %s assigner" %
                      (available_list, assigner_id))
        else:
            # reuse the old ones if fcp_list is not empty
            LOG.info("Found allocated fcps %s for %s, will reuse them."
                     % (fcp_list, assigner_id))
            path_count = self.db.get_path_count()
            if len(fcp_list) != path_count:
                # TODO: handle the case when len(fcp_list) < multipath_count
                LOG.warning("FCPs previously assigned to %s includes %s, "
                            "it is not equal to the path count: %s." %
                            (assigner_id, fcp_list, path_count))
            # we got it from db, let's reuse it
            for old_fcp in fcp_list:
                available_list.append(old_fcp[0])

        return available_list

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

    def get_fcp_dict_in_fcp_list(self, fcp_list):
        """Return a dict of all FCPs in fcp_list

        example (key=FCP, value=path):
        {
            '1a06': 0,
            '1a09': 0,
            '1a07': 0,

            '1b05': 1,
            '1b06': 1,
            '1b0a': 1,
        }
        """

        """
        expanded_fcps example (key=path, value=FCPs):
        {
            0: {'1a06', '1a09', '1a07'},
            1: {'1b05', '1b06', '1b0a'},
        }
        """
        expanded_fcps = self._expand_fcp_list(fcp_list)
        fcp_dict_in_fcp_list = {
            fcp: path for path, fcps in expanded_fcps.items() for fcp in fcps}
        return fcp_dict_in_fcp_list

    def get_fcp_dict_in_db(self):
        """Return a dict of all FCPs in FCP_DB

        example (key=FCP)
        {
            '1a06': ('1a06', 'C2WDL003', 1, 1, 0, ...),
            '1b08': ('1b08', 'C2WDL003', 1, 1, 1, ...),
            '1c08': ('1c08', 'C2WDL003', 1, 1, 2, ...),
            '1a09': ('1a09', '', 0, 0, 0, ...)
        }
        """

        try:
            # Get all FCPs found in DB.
            fcp_in_db = self.db.get_all_fcps_of_assigner()
        except exception.SDKObjectNotExistError:
            fcp_in_db = list()

        fcp_dict_in_db = {fcp[0]: fcp for fcp in fcp_in_db}
        return fcp_dict_in_db

    def get_fcp_dict_in_zvm(self):
        """Return a dict of all FCPs in ZVM

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
        return fcp_dict_in_zvm

    def _sync_db_with_fcp_list(self):
        """Sync FCP DB with FCP list"""

        LOG.info("Enter: Sync FCP DB with FCP list.")

        # Get a dict of all FCPs in fcp_list
        fcp_list = CONF.volume.fcp_list
        fcp_dict_in_fcp_list = self.get_fcp_dict_in_fcp_list(fcp_list)

        # Get a dict of all FCPs in FCP DB
        fcp_dict_in_db = self.get_fcp_dict_in_db()
        LOG.info("fcp_dict_in_db: {}".format(fcp_dict_in_db))

        # Divide FCPs into three sets
        inter_set = set(fcp_dict_in_fcp_list) & set(fcp_dict_in_db)
        del_fcp_set = set(fcp_dict_in_db) - inter_set
        add_fcp_set = set(fcp_dict_in_fcp_list) - inter_set
        LOG.info("FCPs remain unchanged: {}".format(inter_set))
        LOG.info("FCPs to be removed: {}".format(del_fcp_set))
        LOG.info("FCPs to be added: {}".format(add_fcp_set))

        # Update path of existing FCP if path changed
        for fcp in inter_set:
            old_path = fcp_dict_in_db[fcp][4]
            new_path = fcp_dict_in_fcp_list[fcp]
            if old_path != new_path:
                self.db.update_path_of_fcp(fcp, new_path)
                LOG.warn("FCP {} path changed from {} to {}.".format(
                    fcp, old_path, new_path))
        # Delete FCP from DB if connections=0 and reserve=0
        for fcp in del_fcp_set:
            reserve = fcp_dict_in_db[fcp][3]
            connections = fcp_dict_in_db[fcp][2]
            if connections == 0 and reserve == 0:
                self.db.delete(fcp)
                LOG.info("FCP {} removed.".format(fcp))
            else:
                LOG.warn("Ignore the request of "
                         "deleting in-use FCP {}.".format(fcp))
        # Add new FCP into DB
        for fcp in add_fcp_set:
            path = fcp_dict_in_fcp_list[fcp]
            self.db.new(fcp, path)
            LOG.info("FCP {} added.".format(fcp))

        LOG.info("Exit: Sync FCP DB with FCP list.")

    def _sync_db_with_zvm(self):
        """Sync FCP DB with the FCP info queried from zVM"""

        LOG.info("Enter: Sync FCP DB with FCP info queried from z/VM.")

        # Get a dict of all FCPs in FCP DB
        fcp_dict_in_db = self.get_fcp_dict_in_db()

        if not fcp_dict_in_db:
            LOG.info("No FCPs exist in FCP DB. ")
            LOG.info("Exit: Sync FCP DB with FCP info queried from z/VM.")
            return

        LOG.info("Querying FCP status on z/VM.")
        # Get a dict of all FCPs in ZVM
        fcp_dict_in_zvm = self.get_fcp_dict_in_zvm()

        # Update DB column of comment based on the info queried from zVM
        for fcp in fcp_dict_in_db:
            comment_dict = dict()
            if fcp in fcp_dict_in_zvm:
                # Possible state returned by ZVM:
                # 'active', 'free' or 'offline'
                fcp_state = fcp_dict_in_zvm[fcp].get_dev_status()
                comment_dict['state'] = fcp_state
                if fcp_state == 'offline':
                    LOG.warn("FCP {} offline.".format(fcp))
                # Possbile FCP owner returned by ZVM:
                # VM userid: if the FCP is attached to a VM
                # A String "NONE": if the FCP is not attached
                fcp_owner = fcp_dict_in_zvm[fcp].get_owner()
                comment_dict['owner'] = fcp_owner
                # NOTE(cao biao):
                # we assume the WWPN of FCP will not change
                # Hence, only update WWPN if
                # wwpn_npiv column in database is not set
                # and the FCP exists in z/VM
                wwpn_npiv = fcp_dict_in_db[fcp][6]
                if not wwpn_npiv:
                    wwpn_npiv = fcp_dict_in_zvm[fcp].get_npiv_port()
                    wwpn_phy = fcp_dict_in_zvm[fcp].get_physical_port()
                    self.db.update_wwpns_of_fcp(fcp, wwpn_npiv, wwpn_phy)
            else:
                LOG.warn("FCP {} not found in z/VM.".format(fcp))
                comment_dict['state'] = 'notfound'
            self.db.update_comment_of_fcp(fcp, comment_dict)
        # LOG
        fcp_dict_in_db = self.get_fcp_dict_in_db()
        LOG.info("fcp_dict_in_db: {}".format(fcp_dict_in_db))
        LOG.info("Exit: Sync FCP DB with FCP info queried from z/VM.")


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
                connections = self.fcp_mgr.decrease_fcp_usage(fcp, assigner_id)
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
            errmsg = ("Dedicate FCP devices failed with "
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

    def get_volume_connector(self, assigner_id, reserve):
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
            'fcp_paths': 2            # the count of fcp paths
        }
        """

        empty_connector = {'zvm_fcp': [], 'wwpns': [], 'host': '',
                           'phy_to_virt_initiators': {}, 'fcp_paths': 0}
        # get lpar name of the userid, if no host name got, raise exception
        zvm_host = zvmutils.get_lpar_name()
        if zvm_host == '':
            errmsg = "failed to get z/VM LPAR name."
            LOG.error(errmsg)
            raise exception.SDKVolumeOperationError(rs=11,
                                                    userid=assigner_id,
                                                    msg=errmsg)
        # TODO(cao biao): now we have wwpns in database, so we can consider
        # let get_available_fcp return all the FCP info include wwpns,
        # then no need to query database again when get wwpns
        # we even can do reserve or unreserve operations together
        fcp_list = self.fcp_mgr.get_available_fcp(assigner_id, reserve)
        if not fcp_list:
            errmsg = "No available FCP device found."
            LOG.error(errmsg)
            return empty_connector

        # get wwpns of fcp devices
        wwpns = []
        phy_virt_wwpn_map = {}
        for fcp_no in fcp_list:
            wwpn_npiv, wwpn_phy = self.db.get_wwpns_of_fcp(fcp_no)
            if not wwpn_npiv:
                # wwpn_npiv not found in FCP DB
                errmsg = ("NPIV WWPN of FCP device %s not found in "
                          "database." % fcp_no)
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)
            else:
                wwpns.append(wwpn_npiv)
            # We use initiator to build up zones on fabric, for NPIV, the
            # virtual ports are not yet logged in when we creating zones.
            # so we will generate the physical virtual initiator mapping
            # to determine the proper zoning on the fabric.
            # Refer to #7039 for details about avoid creating zones on
            # the fabric to which there is no fcp connected.
            if not wwpn_phy:
                errmsg = ("Physical WWPN of FCP device %s not found in "
                          "database." % fcp_no)
                LOG.error(errmsg)
                raise exception.SDKVolumeOperationError(rs=11,
                                                        userid=assigner_id,
                                                        msg=errmsg)
            else:
                phy_virt_wwpn_map[wwpn_npiv] = wwpn_phy

        # reserve or unreserve FCP record in database
        for fcp_no in fcp_list:
            if reserve:
                # Reserve fcp device
                LOG.info("Reserve fcp device %s for "
                         "instance %s." % (fcp_no, assigner_id))
                self.db.reserve(fcp_no)
                _userid, _reserved, _conns = self.get_fcp_usage(fcp_no)
                LOG.info("After reserve, fcp usage of %s "
                         "is (assigner_id: %s, reserved:%s, connections: %s)."
                         % (fcp_no, _userid, _reserved, _conns))
            elif not reserve and \
                self.db.get_connections_from_fcp(fcp_no) == 0:
                # Unreserve fcp device
                LOG.info("Unreserve fcp device %s from "
                         "instance %s." % (fcp_no, assigner_id))
                self.db.unreserve(fcp_no)
                _userid, _reserved, _conns = self.get_fcp_usage(fcp_no)
                LOG.info("After unreserve, fcp usage of %s "
                         "is (assigner_id: %s, reserved:%s, connections: %s)."
                         % (fcp_no, _userid, _reserved, _conns))

        # return the total path count
        fcp_paths = self.db.get_path_count()
        # return the LPARname+VMuserid as host
        ret_host = zvm_host + '_' + assigner_id
        connector = {'zvm_fcp': fcp_list,
                     'wwpns': wwpns,
                     'phy_to_virt_initiators': phy_virt_wwpn_map,
                     'host': ret_host,
                     'fcp_paths': fcp_paths}
        LOG.info('get_volume_connector returns %s for %s' %
                  (connector, assigner_id))
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

    def _update_raw_fcp_usage(self, raw_usage_by_path, item):
        path_id = item[4]
        if not raw_usage_by_path.get(path_id, None):
            raw_usage_by_path[path_id] = []
        # append item to raw usage
        raw_usage_by_path[path_id].append(item)
        return raw_usage_by_path

    def _update_statistics_usage(self, statistics_usage, item):
        """Tranform raw usage in FCP database into statistic data.
        """
        # get statistic data about:
        #   available, allocated, notfound,
        #   unallocated_but_active, allocated_but_free
        fcp_id, assigner_id, connections, reserved,\
                path_id, comment, _, _ = item
        if comment:
            state = comment.get("state", "").lower()
            owner = comment.get("owner", "")
        else:
            state = ""
            owner = ""
        if not statistics_usage.get(path_id, None):
            statistics_usage[path_id] = {"available": [],
                                         "allocated": [],
                                         "unallocated_but_active": [],
                                         "allocated_but_free": [],
                                         "notfound": [],
                                         "offline": []}
        # case G: (state = notfound)
        # this FCP in database but not found in z/VM
        if state == "notfound":
            statistics_usage[path_id]["notfound"].append(fcp_id)
            LOG.warning("When getting statistics, found a FCP record "
                        "%s with state as notfound in database ." % str(item))
        # case H: (state = offline)
        # this FCP in database but offline in z/VM
        if state == "offline":
            statistics_usage[path_id]["offline"].append(fcp_id)
            LOG.warning("When getting statistics, found state of FCP record "
                        "%s is offline in database." % str(item))
        # found this FCP in z/VM
        if connections == 0:
            if reserved == 0:
                # case A: (reserve=0 and conn=0 and state=free)
                # this FCP is available for use
                if state == "free":
                    statistics_usage[path_id]["available"].append(fcp_id)
                    LOG.debug("When getting statistics, found an available "
                              "FCP record %s in database." % str(item))
                # case E: (conn=0 and reserve=0 and state=active)
                # this FCP is available in database but its state
                # is active in smcli output
                if state == "active":
                    statistics_usage[path_id]["unallocated_but_active"].\
                        append((fcp_id, owner))
                    LOG.warning("When getting statistics, found a FCP record "
                                "%s available in database but its state is "
                                "active, it may be occupied by a userid "
                                "outside of this ZCC." % str(item))
            else:
                # reserver == 1
                # case C: (reserve=1 and conn=0)
                # the fcp should be in task or a bug happen
                LOG.warning("When getting statistics, found a FCP record %s "
                            "may be in tasking." % str(item))
        else:
            # connections != 0
            if reserved == 0:
                # case D: (reserve = 0 and conn != 0)
                # must have a bug result in this
                LOG.warning("When getting statistics, found a FCP record %s "
                            "unreserved in database but its connections "
                            "is not 0." % str(item))
            else:
                # case B: (reserve=1 and conn!=0)
                # ZCC allocated this to a userid
                statistics_usage[path_id]["allocated"].append(fcp_id)
                LOG.debug("When getting statistics, found an allocated "
                          "FCP record: %s." % str(item))
            # case F: (conn!=0 and state=free)
            if state == "free":
                statistics_usage[path_id]["allocated_but_free"].append(
                    fcp_id)
                LOG.warning("When getting statistics, found a FCP record %s "
                            "allocated by ZCC but its state is "
                            "free." % str(item))
            # case I: ((conn != 0) & assigner_id != owner)
            elif assigner_id != owner:
                LOG.warning("When getting statistics, found a FCP record %s "
                            "allocated by ZCC but its assigner differs "
                            "from owner." % str(item))
        return statistics_usage

    def get_all_fcp_usage(self, assigner_id=None, raw=False, statistics=True,
                          sync_with_zvm=False):
        """Get all fcp information grouped by FCP id.
        :param assigner_id: (str) if is None, will get all fcps info in db.
        :param raw: (boolean) if is True, will get raw fcp usage data
        :param statistics: (boolean) if is True, will get statistics data
            of all FCPs
        :param sync_with_zvm: (boolean) if is True, will call SMCLI command
            to sync the FCP state in the database
        :return: (dict) the raw and statistic data of all FCP devices
        The return data example:
        {
            "raw": {
                  # (fcp_id, userid, connections, reserved, path,
                  #  comment, wwpn_npiv, wwpn_phy),
                  0 : (
                    (u'283c',  u'user1', 2, 1, 0,
                     {'state': 'active','owner: 'ABCD0001'},
                     'c05076ddf7003bf4','c05076ddf7001181'),
                    (u'183c',  u'', 0, 0, 0, {'state': 'notfound'},
                     'c05076ddf7004321', 'c05076ddf7001181'),
                  ),
                  1 : (
                    (u'383c',  u'user3', 0, 0, 1,
                     {'state': 'active', 'owner': 'ABCD0001'}),
                     'c05076ddf7001234', 'c05076ddf7001182'
                    (u'483c',  u'user2', 0, 0, 1,
                     {'state': 'free', 'owner': 'NONE'}),
                     'c05076ddf7004322', 'c05076ddf7001182'
                  )
                  ...
            },
            "statistics": {
                0: {
                    # case A: (reserve = 0 and conn = 0 and state = free)
                    # FCP is available and in free status
                    "available": ('1a00','1a05',...)

                    # case B: (reserve = 1 and conn != 0)
                    # nomral in-use FCP
                    "allocated": ('1a00','1a05',...)

                    # case C: (reserve = 1, conn = 0)
                    # the fcp should be in task or a bug cause this situation
                    # will log about this

                    # case D: (reserve = 0 and conn != 0)
                    # should be a bug result in this situation
                    # will log about this

                    # case E: (reserve = 0, conn = 0, state = active)
                    # FCP occupied out-of-band
                    'unallocated_but_active': [('1b04','owner1'),
                                               ('1b05','owner2')]

                    # case F: (conn != 0, state = free)
                    # we allocated it in db but the FCP status is free
                    # this is an situation not expected
                    "allocated_but_free": ('1a00','1a05',...)

                    # case G: (state = notfound)
                    # not found in smcli
                    "notfound": ('1a00','1a05',...)

                    # case H: (state = offline)
                    # offline in smcli
                    "offline": ('1a00','1a05',...)

                    # case I: ((conn != 0) & assigner_id != owner)
                    # assigner_id-in-DB differ from smcli-returned-owner
                    # will log about this
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
                self._update_raw_fcp_usage(raw_usage_by_path, item)
            # get fcp statistics usage
            if statistics:
                self._update_statistics_usage(statistics_usage, item)
        # storage usage into return value
        if raw:
            LOG.debug("Got raw FCP usage: %s" % raw_usage_by_path)
            ret["raw"] = raw_usage_by_path
        if statistics:
            LOG.info("Got statistic FCP usage: %s" % statistics_usage)
            ret["statistics"] = statistics_usage
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
