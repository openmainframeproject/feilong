#    Copyright 2017 IBM Corp.
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
import os

from zvmsdk import config
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

    def volume_refresh_bootmap(self, fcpchannel, wwpn, lun, skipzipl=False):
        return self._volume_manager.volume_refresh_bootmap(fcpchannel,
                                                           wwpn, lun,
                                                           skipzipl=skipzipl)

    def get_volume_connector(self, assigner_id, reserve):
        return self._volume_manager.get_volume_connector(assigner_id, reserve)


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

    def config_attach(self, fcp, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point, new):
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        self.configure_volume_attach(fcp, assigner_id, target_wwpns,
                                     target_lun, multipath, os_version,
                                     mount_point, linuxdist, new)
        # active mode should restart zvmguestconfigure to execute reader file
        if self._vmop.is_reachable(assigner_id):
            active_cmds = linuxdist.create_active_net_interf_cmd()
            self._smtclient.execute_cmd(assigner_id, active_cmds)

    def config_detach(self, fcp, assigner_id, target_wwpns, target_lun,
                      multipath, os_version, mount_point, connections):
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        self.configure_volume_detach(fcp, assigner_id, target_wwpns,
                                     target_lun, multipath, os_version,
                                     mount_point, linuxdist, connections)
        # active mode should restart zvmguestconfigure to execute reader file
        if self._vmop.is_reachable(assigner_id):
            active_cmds = linuxdist.create_active_net_interf_cmd()
            self._smtclient.execute_cmd(assigner_id, active_cmds)

    def _create_file(self, assigner_id, file_name, data):
        temp_folder = self._smtclient.get_guest_temp_path(assigner_id)
        file_path = os.path.join(temp_folder, file_name)
        with open(file_path, "w") as f:
            f.write(data)
        return file_path, temp_folder

    def configure_volume_attach(self, fcp, assigner_id, target_wwpns,
                                target_lun, multipath, os_version,
                                mount_point, linuxdist, new):
        """new==True means this is first attachment"""
        # get configuration commands
        config_cmds = linuxdist.get_volume_attach_configuration_cmds(
                          fcp, target_wwpns, target_lun, multipath,
                          mount_point, new)
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

    def configure_volume_detach(self, fcp, assigner_id, target_wwpns,
                                target_lun, multipath, os_version,
                                mount_point, linuxdist, connections):
        # get configuration commands
        config_cmds = linuxdist.get_volume_detach_configuration_cmds(
                          fcp, target_wwpns, target_lun, multipath,
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
        self._npiv_port = None
        self._chpid = None
        self._physical_port = None
        self._assigned_id = None

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
    def _get_chpid_from_line(info_line):
        chpid = info_line.split(':')[-1].strip().upper()
        return chpid if chpid else None

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
        if isinstance(init_info, list) and (len(init_info) == 5):
            self._dev_no = self._get_dev_number_from_line(init_info[0])
            self._npiv_port = self._get_wwpn_from_line(init_info[2])
            self._chpid = self._get_chpid_from_line(init_info[3])
            self._physical_port = self._get_wwpn_from_line(init_info[4])

    def get_dev_no(self):
        return self._dev_no

    def get_npiv_port(self):
        return self._npiv_port

    def get_physical_port(self):
        return self._physical_port

    def get_chpid(self):
        return self._chpid

    def is_valid(self):
        # FIXME: add validation later
        return True


class FCPManager(object):

    def __init__(self):
        # _fcp_pool store the objects of FCP index by fcp id
        self._fcp_pool = {}
        # _fcp_path_info store the FCP path mapping index by path no
        self._fcp_path_mapping = {}
        self.db = database.FCPDbOperator()
        self._smtclient = smtclient.get_smtclient()

    def init_fcp(self, assigner_id):
        """init_fcp to init the FCP managed by this host"""
        # TODO master_fcp_list (zvm_zhcp_fcp_list) really need?
        fcp_list = CONF.volume.fcp_list
        if fcp_list == '':
            errmsg = ("because CONF.volume.fcp_list is empty, "
                      "no volume functions available")
            LOG.info(errmsg)
            return

        self._init_fcp_pool(fcp_list, assigner_id)
        self._sync_db_fcp_list()

    def _init_fcp_pool(self, fcp_list, assigner_id):
        """The FCP infomation got from smt(zthin) looks like :
           host: FCP device number: xxxx
           host:   Status: Active
           host:   NPIV world wide port number: xxxxxxxx
           host:   Channel path ID: xx
           host:   Physical world wide port number: xxxxxxxx
           ......
           host: FCP device number: xxxx
           host:   Status: Active
           host:   NPIV world wide port number: xxxxxxxx
           host:   Channel path ID: xx
           host:   Physical world wide port number: xxxxxxxx

        """
        self._fcp_path_mapping = self._expand_fcp_list(fcp_list)
        complete_fcp_set = set()
        for path, fcp_set in self._fcp_path_mapping.items():
            complete_fcp_set = complete_fcp_set | fcp_set
        fcp_info = self._get_all_fcp_info(assigner_id)
        lines_per_item = 5
        # after process, _fcp_pool should be a list include FCP ojects
        # whose FCP ID are from CONF.volume.fcp_list and also should be
        # found in fcp_info
        num_fcps = len(fcp_info) // lines_per_item
        for n in range(0, num_fcps):
            fcp_init_info = fcp_info[(5 * n):(5 * (n + 1))]
            fcp = FCP(fcp_init_info)
            dev_no = fcp.get_dev_no()
            if dev_no in complete_fcp_set:
                if fcp.is_valid():
                    self._fcp_pool[dev_no] = fcp
                else:
                    errmsg = ("Find an invalid FCP device with properties {"
                              "dev_no: %(dev_no)s, "
                              "NPIV_port: %(NPIV_port)s, "
                              "CHPID: %(CHPID)s, "
                              "physical_port: %(physical_port)s} !") % {
                               'dev_no': fcp.get_dev_no(),
                               'NPIV_port': fcp.get_npiv_port(),
                               'CHPID': fcp.get_chpid(),
                               'physical_port': fcp.get_physical_port()}
                    LOG.warning(errmsg)
            else:
                # normal, FCP not used by cloud connector at all
                msg = "Found a fcp %s not in fcp_list" % dev_no
                LOG.debug(msg)

    @staticmethod
    def _expand_fcp_list(fcp_list):
        """Expand fcp list string into a python list object which contains
        each fcp devices in the list string. A fcp list is composed of fcp
        device addresses, range indicator '-', and split indicator ';'.

        For example, if fcp_list is
        "0011-0013;0015;0017-0018", expand_fcp_list(fcp_list) will return
        [0011, 0012, 0013, 0015, 0017, 0018].

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
            return set()
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

    def _report_orphan_fcp(self, fcp):
        """check there is record in db but not in FCP configuration"""
        LOG.warning("WARNING: fcp %s found in db but not in "
                    "CONF.volume.fcp_list which is %s" %
                    (fcp, CONF.volume.fcp_list))

    def _add_fcp(self, fcp, path):
        """add fcp to db if it's not in db but in fcp list and init it"""
        try:
            LOG.info("fcp %s found in CONF.volume.fcp_list, add it to db" %
                     fcp)
            self.db.new(fcp, path)
        except Exception:
            LOG.info("failed to add fcp %s into db", fcp)

    def _sync_db_fcp_list(self):
        """sync db records from given fcp list, for example, you need
        warn if some FCP already removed while it's still in use,
        or info about the new FCP added"""
        fcp_db_list = self.db.get_all()

        for fcp_rec in fcp_db_list:
            if not fcp_rec[0].lower() in self._fcp_pool:
                self._report_orphan_fcp(fcp_rec[0])
        # firt loop is for getting the path No
        for path, fcp_list in self._fcp_path_mapping.items():
            for fcp in fcp_list:
                if fcp.lower() in self._fcp_pool:
                    res = self.db.get_from_fcp(fcp)
                    # if not found this record, a [] will be returned
                    if len(res) == 0:
                        # now only support 2 paths
                        self._add_fcp(fcp, path)

    def _list_fcp_details(self, userid, status):
        return self._smtclient.get_fcp_info_by_status(userid, status)

    def _get_all_fcp_info(self, assigner_id):
        fcp_info = []
        free_fcp_info = self._list_fcp_details(assigner_id, 'free')
        active_fcp_info = self._list_fcp_details(assigner_id, 'active')

        if free_fcp_info:
            fcp_info.extend(free_fcp_info)

        if active_fcp_info:
            fcp_info.extend(active_fcp_info)

        return fcp_info

    def find_and_reserve_fcp(self, assigner_id):
        """reserve the fcp to assigner_id

        The function to reserve a fcp for user
        1. Check whether assigner_id has a fcp already
           if yes, make the reserve of that record to 1
        2. No fcp, then find a fcp and reserve it

        fcp will be returned, or None indicate no fcp
        """
        fcp_list = self.db.get_from_assigner(assigner_id)
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
        # get the sum of connections belong to assinger_id
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

    def get_available_fcp(self, assigner_id):
        """get all the fcps not reserved, choose one from path0
           and choose another from path1, compose a pair to return.
           result will only have two FCP IDs, looks like [0011, 0021]
        """
        available_list = []
        # first check whether this userid already has a FCP device
        # get the FCP devices belongs to assigner_id
        fcp_list = self.db.get_from_assigner(assigner_id)
        if not fcp_list:
            free_unreserved = self.db.get_fcp_pair()
            for item in free_unreserved:
                available_list.append(item)
                # record the assigner id in the fcp so that
                # when the vm provision with both root and data volumes
                # the root and data volume would get the same FCP devices
                # with the get_volume_connector call.
                self.db.assign(item, assigner_id, update_connections=False)

            LOG.debug("allocated %s fcp for %s assigner" %
                      (available_list, assigner_id))
        else:
            path_count = self.db.get_path_count()
            if len(fcp_list) < path_count:
                # TODO: handle the case when len(fcp_list) < multipath_count
                LOG.warning("FCPs assigned to %s includes %s, "
                            "it is less than the path count: %s." %
                            (assigner_id, fcp_list, path_count))
            # we got it from db, let's reuse it
            for old_fcp in fcp_list:
                available_list.append(old_fcp[0])

        return available_list

    def get_wwpn(self, fcp_no):
        fcp = self._fcp_pool.get(fcp_no)
        if not fcp:
            return None
        npiv = fcp.get_npiv_port()
        physical = fcp.get_physical_port()
        if npiv:
            return npiv
        if physical:
            return physical
        return None


# volume manager for FCP protocol
class FCPVolumeManager(object):
    def __init__(self):
        self.fcp_mgr = FCPManager()
        self.config_api = VolumeConfiguratorAPI()
        self._smtclient = smtclient.get_smtclient()
        self.db = database.FCPDbOperator()

    def _dedicate_fcp(self, fcp, assigner_id):
        self._smtclient.dedicate_device(assigner_id, fcp, fcp, 0)

    def _add_disk(self, fcp, assigner_id, target_wwpns, target_lun,
                  multipath, os_version, mount_point, new):
        self.config_api.config_attach(fcp, assigner_id, target_wwpns,
                                      target_lun, multipath, os_version,
                                      mount_point, new)

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

    def _attach(self, fcp, assigner_id, target_wwpns, target_lun,
                multipath, os_version, mount_point, path_count,
                is_root_volume):
        """Attach a volume

        First, we need translate fcp into local wwpn, then
        dedicate fcp to the user if it's needed, after that
        call smt layer to call linux command
        """
        LOG.info('Start to attach device to %s' % assigner_id)
        # TODO: init_fcp should be called in contructor function
        # but no assinger_id in contructor
        self.fcp_mgr.init_fcp(assigner_id)
        new = self.fcp_mgr.add_fcp_for_assigner(fcp, assigner_id)
        if is_root_volume:
            LOG.info('Attaching device to %s is done.' % assigner_id)
            return new
        try:
            if new:
                self._dedicate_fcp(fcp, assigner_id)

            self._add_disk(fcp, assigner_id, target_wwpns, target_lun,
                           multipath, os_version, mount_point, new)
        except exception.SDKBaseException as err:
            errmsg = 'Attach failed with error:' + err.format_message()
            LOG.error(errmsg)
            self._rollback_dedicated_fcp([fcp], assigner_id)
            raise exception.SDKBaseException(msg=errmsg)
        # TODO: other exceptions?

        LOG.info('Attaching device to %s is done.' % assigner_id)
        return new

    def volume_refresh_bootmap(self, fcpchannels, wwpns, lun, skipzipl=False):
        """ Refresh a volume's bootmap info.

        :param list of fcpchannels
        :param list of wwpns
        :param string lun
        :param boolean skipzipl: whether ship zipl, only return physical wwpns
        """
        return self._smtclient.volume_refresh_bootmap(fcpchannels, wwpns, lun,
                                                      skipzipl=skipzipl)

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
        target_wwpns = connection_info['target_wwpn']
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
            dedicated_fcp = []
            for i in range(path_count):
                try:
                    new = self._attach(fcp[i].lower(), assigner_id,
                                       target_wwpns, target_lun, multipath,
                                       os_version, mount_point, path_count,
                                       is_root_volume)
                    if new and is_root_volume is False:
                        dedicated_fcp.append(fcp[i])
                except exception.SDKBaseException:
                    self._rollback_dedicated_fcp(dedicated_fcp, assigner_id,
                        all_fcp_list=fcp)
                    raise

    def _undedicate_fcp(self, fcp, assigner_id):
        self._smtclient.undedicate_device(assigner_id, fcp)

    def _remove_disk(self, fcp, assigner_id, target_wwpns, target_lun,
                     multipath, os_version, mount_point, connections):
        self.config_api.config_detach(fcp, assigner_id, target_wwpns,
                                      target_lun, multipath, os_version,
                                      mount_point, connections)

    def _detach(self, fcp, assigner_id, target_wwpns, target_lun,
                multipath, os_version, mount_point, is_root_volume):
        """Detach a volume from a guest"""
        LOG.info('Start to detach device from %s' % assigner_id)
        connections = self.fcp_mgr.decrease_fcp_usage(fcp, assigner_id)
        if is_root_volume:
            LOG.info('Detaching device from %s is done.' % assigner_id)
            return

        try:
            self._remove_disk(fcp, assigner_id, target_wwpns, target_lun,
                              multipath, os_version, mount_point, connections)
            if not connections:
                self._undedicate_fcp(fcp, assigner_id)
        except (exception.SDKBaseException,
                exception.SDKSMTRequestFailed) as err:
            errmsg = 'detach failed with error:' + err.format_message()
            LOG.error(errmsg)
            self.fcp_mgr.increase_fcp_usage(fcp, assigner_id)
            with zvmutils.ignore_errors():
                new = (connections == 0)
                self._add_disk(fcp, assigner_id, target_wwpns, target_lun,
                               multipath, os_version, mount_point, new)
            raise exception.SDKBaseException(msg=errmsg)

        # Unreserved fcp device after undedicate all FCP devices
        if not connections:
            LOG.info("Unreserve fcp device %s from detach", fcp)
            self.fcp_mgr.unreserve_fcp(fcp)
        LOG.info('Detaching device from %s is done.' % assigner_id)

    def detach(self, connection_info):
        """Detach a volume from a guest
        """
        fcp = connection_info['zvm_fcp']
        target_wwpns = connection_info['target_wwpn']
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
        if is_root_volume is False and \
                not zvmutils.check_userid_exist(assigner_id):
            LOG.error("Guest '%s' does not exist" % assigner_id)
            raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % assigner_id), modID='volume')
        else:
            # TODO: now we only support 2 paths
            path_count = len(fcp)
            for i in range(path_count):
                self._detach(fcp[i].lower(), assigner_id, target_wwpns,
                             target_lun, multipath, os_version, mount_point,
                             is_root_volume)

    def get_volume_connector(self, assigner_id, reserve):
        """Get connector information of the instance for attaching to volumes.

        Connector information is a dictionary representing the ip of the
        machine that will be making the connection, the name of the iscsi
        initiator and the hostname of the machine as follows::

            {
                'zvm_fcp': [fcp]
                'wwpns': [wwpn]
                'host': host
            }
        """

        empty_connector = {'zvm_fcp': [], 'wwpns': [], 'host': ''}

        # init fcp pool
        self.fcp_mgr.init_fcp(assigner_id)
        # fcp = self.fcp_mgr.find_and_reserve_fcp(assigner_id)
        fcp_list = self.fcp_mgr.get_available_fcp(assigner_id)
        if not fcp_list:
            errmsg = "No available FCP device found."
            LOG.error(errmsg)
            return empty_connector
        wwpns = []
        for fcp_no in fcp_list:
            if reserve:
                # Reserve fcp device
                LOG.info("Reserve fcp device %s", fcp_no)
                self.db.reserve(fcp_no)
            elif not reserve and \
                self.db.get_connections_from_fcp(fcp_no) == 0:
                # Unreserve fcp device
                LOG.info("Unreserve fcp device %s from get connector", fcp_no)
                self.db.unreserve(fcp_no)
            wwpn = self.fcp_mgr.get_wwpn(fcp_no)
            if not wwpn:
                errmsg = "FCP device %s has no available WWPN." % fcp_no
                LOG.error(errmsg)
            else:
                wwpns.append(wwpn)

        if not wwpns:
            errmsg = "No available WWPN found."
            LOG.error(errmsg)
            return empty_connector

        inv_info = self._smtclient.get_host_info()
        zvm_host = inv_info['zvm_host']
        if zvm_host == '':
            errmsg = "zvm host not specified."
            LOG.error(errmsg)
            return empty_connector

        connector = {'zvm_fcp': fcp_list,
                     'wwpns': wwpns,
                     'host': zvm_host}
        LOG.debug('get_volume_connector returns %s for %s' %
                  (connector, assigner_id))
        return connector
