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
import six

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import database
from zvmsdk import dist
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import smutclient
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

    def config_attach(self, fcp, assigner_id, target_wwpn, target_lun,
                      multipath, os_version, mount_point):
        if self._vmop.is_reachable(assigner_id):
            self.config_attach_active(fcp, assigner_id, target_wwpn,
                                      target_lun, multipath, os_version,
                                      mount_point)
        else:
            self.config_attach_inactive(fcp, assigner_id, target_wwpn,
                                        target_lun, multipath, os_version,
                                        mount_point)

    def config_force_attach(self, fcp, assigner_id, target_wwpn, target_lun,
                            multipath, os_version):
        pass

    def config_detach(self, fcp, assigner_id, target_wwpn, target_lun,
                      multipath, os_version, mount_point):
        if self._vmop.is_reachable(assigner_id):
            self.config_detach_active(fcp, assigner_id, target_wwpn,
                                      target_lun, multipath, os_version,
                                      mount_point)
        else:
            self.config_detach_inactive(fcp, assigner_id, target_wwpn,
                                        target_lun, multipath, os_version,
                                        mount_point)

    def config_force_detach(self, fcp, assigner_id, target_wwpn, target_lun,
                            multipath, os_version):
        pass

    def config_attach_active(self, fcp, assigner_id, target_wwpn,
                             target_lun, multipath, os_version, mount_point):
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        linuxdist.config_volume_attach_active(fcp, assigner_id, target_wwpn,
                                              target_lun, multipath,
                                              mount_point)

    def config_attach_inactive(self, fcp, assigner_id, target_wwpn,
                               target_lun, multipath, os_version, mount_point):
        raise NotImplementedError

    def config_detach_active(self, fcp, assigner_id, target_wwpn,
                             target_lun, multipath, os_version,
                             mount_point):
        linuxdist = self._dist_manager.get_linux_dist(os_version)()
        linuxdist.config_volume_detach_active(fcp, assigner_id, target_wwpn,
                                              target_lun, multipath,
                                              mount_point)

    def config_detach_inactive(self, fcp, assigner_id, target_wwpn,
                               target_lun, multipath, os_version,
                               mount_point):
        raise NotImplementedError


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

    def is_valid(self):
        # FIXME: add validation later
        return True


class FCPManager(object):

    def __init__(self):
        self._fcp_pool = {}
        self.db = database.FCPDbOperator()
        self._smutclient = smutclient.get_smutclient()

    def init_fcp(self, assigner_id):
        """init_fcp to init the FCP managed by this host"""
        # TODO master_fcp_list (zvm_zhcp_fcp_list) really need?
        fcp_list = CONF.volume.fcp_list
        if fcp_list == '':
            errmsg = ("because CONF.volume.fcp_list is empty, "
                      "no volume functions available")
            LOG.info(errmsg)
            return

        self._fcp_info = self._init_fcp_pool(fcp_list, assigner_id)
        self._sync_db_fcp_list()

    def _init_fcp_pool(self, fcp_list, assigner_id):
        """The FCP infomation got from smut(zthin) looks like :
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
        complete_fcp_set = self._expand_fcp_list(fcp_list)
        fcp_info = self._get_all_fcp_info(assigner_id)
        lines_per_item = 5

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

        """

        LOG.debug("Expand FCP list %s" % fcp_list)

        if not fcp_list:
            return set()

        range_pattern = '[0-9a-fA-F]{1,4}(-[0-9a-fA-F]{1,4})?'
        match_pattern = "^(%(range)s)(;%(range)s)*$" % {'range': range_pattern}
        if not re.match(match_pattern, fcp_list):
            errmsg = ("Invalid FCP address %s") % fcp_list
            raise exception.SDKInternalError(msg=errmsg)

        fcp_devices = set()
        for _range in fcp_list.split(';'):
            if '-' not in _range:
                # single device
                fcp_addr = int(_range, 16)
                fcp_devices.add("%04x" % fcp_addr)
            else:
                # a range of address
                (_min, _max) = _range.split('-')
                _min = int(_min, 16)
                _max = int(_max, 16)
                for fcp_addr in range(_min, _max + 1):
                    fcp_devices.add("%04x" % fcp_addr)

        # remove duplicate entries
        return fcp_devices

    def _report_orphan_fcp(self, fcp):
        """check there is record in db but not in FCP configuration"""
        LOG.warning("WARNING: fcp %s found in db but not in "
                    "CONF.volume.fcp_list which is %s" %
                    (fcp, CONF.volume.fcp_list))

    def _add_fcp(self, fcp):
        """add fcp to db if it's not in db but in fcp list and init it"""
        try:
            LOG.info("fcp %s found in CONF.volume.fcp_list, add it to db" %
                     fcp)
            self.db.new(fcp)
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

        for fcp_conf_rec, v in self._fcp_pool.items():
            res = self.db.get_from_fcp(fcp_conf_rec)

            # if not found this record, a [] will be returned
            if len(res) == 0:
                self._add_fcp(fcp_conf_rec)

    def _list_fcp_details(self, userid, status):
        return self._smutclient.get_fcp_info_by_status(userid, status)

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
        connections = self.db.get_connections_from_assigner(assigner_id)
        new = False

        if connections == 0:
            self.db.assign(fcp, assigner_id)
            new = True
        else:
            self.db.increase_usage(fcp)

        return new

    def decrease_fcp_usage(self, fcp, assigner_id=None):
        # TODO: check assigner_id to make sure on the correct fcp record
        connections = self.db.decrease_usage(fcp)

        return connections

    def unreserve_fcp(self, fcp, assigner_id=None):
        # TODO: check assigner_id to make sure on the correct fcp record
        self.db.unreserve(fcp)


# volume manager for FCP protocol
class FCPVolumeManager(object):
    def __init__(self):
        self.fcp_mgr = FCPManager()
        self.config_api = VolumeConfiguratorAPI()
        self._smutclient = smutclient.get_smutclient()

    def _dedicate_fcp(self, fcp, assigner_id):
        self._smutclient.dedicate_device(assigner_id, fcp, fcp, 0)

    def _add_disk(self, fcp, assigner_id, target_wwpn, target_lun,
                  multipath, os_version, mount_point):
        self.config_api.config_attach(fcp, assigner_id, target_wwpn,
                                      target_lun, multipath, os_version,
                                      mount_point)

    def _attach(self, fcp, assigner_id, target_wwpn, target_lun,
                multipath, os_version, mount_point):
        """Attach a volume

        First, we need translate fcp into local wwpn, then
        dedicate fcp to the user if it's needed, after that
        call smut layer to call linux command
        """
        LOG.info('Start to attach device to %s' % assigner_id)
        self.fcp_mgr.init_fcp(assigner_id)
        new = self.fcp_mgr.increase_fcp_usage(fcp, assigner_id)
        try:
            if new:
                self._dedicate_fcp(fcp, assigner_id)

            self._add_disk(fcp, assigner_id, target_wwpn, target_lun,
                           multipath, os_version, mount_point)
        except exception.SDKBaseException as err:
            errmsg = 'rollback attach because error:' + err.format_message()
            LOG.error(errmsg)
            connections = self.fcp_mgr.decrease_fcp_usage(fcp, assigner_id)
            # if connections less than 1, undedicate the device
            if not connections:
                with zvmutils.ignore_errors():
                    self._undedicate_fcp(fcp, assigner_id)
            raise exception.SDKBaseException(msg=errmsg)

        LOG.info('Attaching device to %s is done.' % assigner_id)

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
        fcp = fcp.lower()
        target_wwpn = connection_info['target_wwpn']
        target_lun = connection_info['target_lun']
        assigner_id = connection_info['assigner_id']
        multipath = connection_info['multipath']
        os_version = connection_info['os_version']
        mount_point = connection_info['mount_point']

        self._attach(fcp, assigner_id, target_wwpn, target_lun,
                     multipath, os_version, mount_point)

    def _undedicate_fcp(self, fcp, assigner_id):
        self._smutclient.undedicate_device(assigner_id, fcp)

    def _remove_disk(self, fcp, assigner_id, target_wwpn, target_lun,
                     multipath, os_version, mount_point):
        self.config_api.config_detach(fcp, assigner_id, target_wwpn,
                                      target_lun, multipath, os_version,
                                      mount_point)

    def _detach(self, fcp, assigner_id, target_wwpn, target_lun,
                multipath, os_version, mount_point):
        """Detach a volume from a guest"""
        LOG.info('Start to detach device from %s' % assigner_id)
        connections = self.fcp_mgr.decrease_fcp_usage(fcp, assigner_id)

        try:
            self._remove_disk(fcp, assigner_id, target_wwpn, target_lun,
                              multipath, os_version, mount_point)
            if not connections:
                self._undedicate_fcp(fcp, assigner_id)
        except (exception.SDKBaseException,
                exception.SDKSMUTRequestFailed) as err:
            errmsg = 'rollback detach because error:' + err.format_message()
            LOG.error(errmsg)
            self.fcp_mgr.increase_fcp_usage(fcp, assigner_id)
            with zvmutils.ignore_errors():
                self._add_disk(fcp, assigner_id, target_wwpn, target_lun,
                               multipath, os_version, mount_point)
            raise exception.SDKBaseException(msg=errmsg)

        LOG.info('Detaching device to %s is done.' % assigner_id)

    def detach(self, connection_info):
        """Detach a volume from a guest
        """
        fcp = connection_info['zvm_fcp']
        fcp = fcp.lower()
        target_wwpn = connection_info['target_wwpn']
        target_lun = connection_info['target_lun']
        assigner_id = connection_info['assigner_id']
        multipath = connection_info['multipath']
        os_version = connection_info['os_version']
        mount_point = connection_info['mount_point']

        self._detach(fcp, assigner_id, target_wwpn, target_lun, multipath,
                     os_version, mount_point)

    def get_volume_connector(self, assigner_id):
        """Get volume connector, mainly get a fcp

        """
        fcp = self.fcp_mgr.find_and_reserve_fcp(assigner_id)
        res = {'platform': constants.ARCHITECTURE,
               'ip': CONF.network.my_ip,
               'do_local_attach': False,
               'os_type': 'linux',
               # FIXME:
               'os_version': '',
               'multipath': True,
               'fcp': fcp}
        LOG.debug('get_volume_connector returns %s for %s' %
                  (fcp, assigner_id))
        return res
