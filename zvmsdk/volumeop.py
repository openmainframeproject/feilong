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
from zvmsdk import database
from zvmsdk import exception
from zvmsdk import log
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
        _VolumeOP = VolumeOperator()
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

    @abc.abstractmethod
    def attach_volume_to_instance(self, instance, volume, connection_info,
                                  is_rollback_in_failure=False):
        raise NotImplementedError

    @abc.abstractmethod
    def detach_volume_from_instance(self, instance, volume, connection_info,
                                    is_rollback_in_failure=False):
        raise NotImplementedError


@six.add_metaclass(abc.ABCMeta)
class VolumeConfiguratorAPI(object):
    """Volume configure APIs to implement volume config jobs on the
    target instance, like: attach, detach, and so on.

    The reason to design these APIs is to hide the details among
    different Linux distributions and releases.
    """

    @abc.abstractmethod
    def config_attach(self, instance, volume, connection_info):
        raise NotImplementedError

    @abc.abstractmethod
    def config_force_attach(self, instance, volume, connection_info):
        # roll back when detaching fails
        raise NotImplementedError

    @abc.abstractmethod
    def config_detach(self, instance, volume, connection_info):
        raise NotImplementedError

    @abc.abstractmethod
    def config_force_detach(self, instance, volume, connection_info):
        # roll back when attaching fails
        raise NotImplementedError


class _BaseConfigurator(VolumeConfiguratorAPI):
    """Contain common code for all distros."""

    def __init__(self):
        self._vmop = vmops.get_vmops()

    def config_attach(self, instance, volume, connection_info):
        if self._vmop.is_reachable(instance[NAME]):
            self.config_attach_active(instance, volume, connection_info)
        else:
            self.config_attach_inactive(instance, volume, connection_info)

    def config_force_attach(self, instance, volume, connection_info):
        pass

    def config_detach(self, instance, volume, connection_info):
        if self._vmop.is_reachable(instance[NAME]):
            self.config_detach_active(instance, volume, connection_info)
        else:
            self.config_detach_inactive(instance, volume, connection_info)

    def config_force_detach(self, instance, volume, connection_info):
        pass

    def config_attach_active(self, instance, volume, connection_info):
        raise NotImplementedError

    def config_attach_inactive(self, instance, volume, connection_info):
        raise NotImplementedError

    def config_detach_active(self, instance, volume, connection_info):
        raise NotImplementedError

    def config_detach_inactive(self, instance, volume, connection_info):
        raise NotImplementedError


class _Configurator_RHEL7(_BaseConfigurator):

    def config_attach_active(self, instance, volume, connection_info):
        pass

    def config_attach_inactive(self, instance, volume, connection_info):
        pass

    def config_detach_active(self, instance, volume, connection_info):
        pass

    def config_detach_inactive(self, instance, volume, connection_info):
        pass


class _Configurator_SLES12(_BaseConfigurator):

    def config_attach_active(self, instance, volume, connection_info):
        pass

    def config_attach_inactive(self, instance, volume, connection_info):
        pass

    def config_detach_active(self, instance, volume, connection_info):
        pass

    def config_detach_inactive(self, instance, volume, connection_info):
        pass


class _Configurator_Ubuntu16(_BaseConfigurator):

    def config_attach_active(self, instance, volume, connection_info):
        pass

    def config_attach_inactive(self, instance, volume, connection_info):
        pass


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

    def _init_fcp_pool(self, fcp_list):
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
        fcp_info = self._get_all_fcp_info()
        lines_per_item = 5

        num_fcps = len(fcp_info) / lines_per_item
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

    def _get_all_fcp_info(self):
        fcp_info = []
        free_fcp_info = self._list_fcp_details('free')
        active_fcp_info = self._list_fcp_details('active')

        if free_fcp_info:
            fcp_info.extend(free_fcp_info)

        if active_fcp_info:
            fcp_info.extend(active_fcp_info)

        return fcp_info

    def init_fcp(self, host_stats):
        """init_fcp to init the FCP managed by this host"""
        # TODO master_fcp_list (zvm_zhcp_fcp_list) really need?
        fcp_list = CONF.volume.fcp_list
        if fcp_list is None:
            errmsg = ("because CONF.volume.fcp_list is empty, "
                      "no volume functions available")
            LOG.Info(errmsg)
            return

        self._fcp_info = self._init_fcp_pool(fcp_list)

    def find_and_reserve_fcp(self):
        """reserve a FCP, note we assume upper layer will reserve a
        FCP first then allocate it because some consumer such as openstack
        need this kind of functions"""
        fcp = self.db.find_and_reserve()
        return fcp

    def allocate_fcp(self, fcp):
        """allocate the fcp to user or increase fcp usage"""
        pass

    def deallocate_fcp(self, userid):
        pass


class VolumeOperator(VolumeOperatorAPI):

    __singleton = None

    _PATTERN_RHEL7 = '^rhel7(\.[0-9])?$'
    _PATTERN_SLES12 = '^sles12(sp[1-9])?$'
    _PATTERN_UBUNTU16 = '^ubuntu16(\.[0-9][0-9])?$'

    def __new__(cls, *args, **kwargs):
        if not cls.__singleton:
            cls.__singleton = super(VolumeOperator, cls
                                    ).__new__(cls, *args, **kwargs)
        return cls.__singleton

    def attach_volume_to_instance(self,
                                  instance,
                                  volume,
                                  connection_info,
                                  is_rollback_in_failure=False):
        LOG.debug("Enter VolumeOperator.attach_volume_to_instance, attach "
                  "volume %(vol)s to instance %(inst)s by connection_info "
                  "%(conn_info)s.")

        self._validate_instance(instance)
        self._validate_volume(volume)
        self._validate_connection_info(connection_info)

        configurator = self._get_configurator(instance)
        configurator.config_attach(instance, volume, connection_info)

        LOG.debug("Exit VolumeOperator.attach_volume_to_instance.")

    def detach_volume_from_instance(self,
                                    instance,
                                    volume,
                                    connection_info,
                                    is_rollback_in_failure=False):
        LOG.debug("Enter VolumeOperator.detach_volume_from_instance, detach "
                  "volume %(vol)s from instance %(inst)s by connection_info "
                  "%(conn_info)s.")

        self._validate_instance(instance)
        self._validate_volume(volume)
        self._validate_connection_info(connection_info)

        configurator = self._get_configurator(instance)
        configurator.config_detach(instance, volume, connection_info)

        LOG.debug("Exit VolumeOperator.detach_volume_from_instance.")

    def _validate_instance(self, instance):
        # arg type checks are done in API level

        if OS_TYPE not in instance.keys():
            raise exception.SDKInvalidInputFormat(
                "instance os_type is not passed in!")

        if NAME not in instance.keys():
            raise exception.SDKInvalidInputFormat(
                "instance name is not passed in!")

        # os_type patterns for rhel7, sles12 and ubuntu 16, i.e.
        # rhel7: rhel7, rhel7.2
        # sles12: sles12, sles12sp2
        # ubuntu16: ubuntu16, ubuntu16.04
        os_type_pattern = (self._PATTERN_RHEL7 +
                           '|' + self._PATTERN_SLES12 +
                           '|' + self._PATTERN_UBUNTU16)
        if not re.match(os_type_pattern, instance[OS_TYPE]):
            msg = ("unknown instance os_type: %s . It must be one of set "
                   "'rhel7, sles12, or ubuntu16'." % instance[OS_TYPE])
            raise exception.SDKInvalidInputFormat(msg)

    def _is_16bit_hex(self, value):
        pattern = '^[0-9a-f]{16}$'
        try:
            return re.match(pattern, value)
        except Exception:
            return False

    def _validate_volume(self, volume):
        # arg type checks are done in API level

        if TYPE not in volume.keys():
            raise exception.SDKInvalidInputFormat(
                "volume type is not passed in!")

        # support only FiberChannel volumes at this moment
        if volume[TYPE] != 'fc':
            msg = ("volume type: %s is illegal!" % volume[TYPE])
            raise exception.SDKInvalidInputFormat(msg)
        self._validate_fc_volume(volume)

    def _validate_fc_volume(self, volume):
        # exclusively entering from _validate_volume at this moment, so will
        # not check volume object again. Modify it if necessary in the future
        if LUN not in volume.keys():
            raise exception.SDKInvalidInputFormat(
                "volume LUN is not passed in!")

        volume[LUN] = volume[LUN].lower()
        if not self._is_16bit_hex(volume[LUN]):
            msg = ("volume LUN value: %s is illegal!" % volume[LUN])
            raise exception.SDKInvalidInputFormat(msg)

    def _validate_connection_info(self, connection_info):
        # arg type checks are done in API level

        if ALIAS not in connection_info.keys():
            raise exception.SDKInvalidInputFormat(
                "device alias is not passed in!")

        if PROTOCOL not in connection_info.keys():
            raise exception.SDKInvalidInputFormat(
                "connection protocol is not passed in!")

        # support only FiberChannel volumes at this moment
        if connection_info[PROTOCOL] != 'fc':
            raise exception.SDKInvalidInputFormat(
                "connection protocol: %s is illegal!" %
                connection_info[PROTOCOL])
        self._validate_fc_connection_info(connection_info)

    def _validate_fc_connection_info(self, connection_info):
        # exclusively entering from _validate_connection_info at this moment,
        # so will not check connection_info object again. Modify it if
        # necessary in the future
        if DEDICATE in connection_info.keys():
            if not isinstance(connection_info[DEDICATE], list):
                msg = ("dedicate devices in connection info must be of type "
                       "list, however the object passed in is: %s !"
                       % connection_info[DEDICATE])
                raise exception.SDKInvalidInputFormat(msg)
            for i in range(len(connection_info[DEDICATE])):
                connection_info[DEDICATE][i] = (
                        connection_info[DEDICATE][i].lower())

        if FCPS not in connection_info.keys():
            raise exception.SDKInvalidInputFormat(
                "fcp devices are not passed in!")

        if not isinstance(connection_info[FCPS], list):
            msg = ("fcp devices in connection info must be of type list, "
                   "however the object passed in is: %s !"
                   % connection_info[FCPS])
            raise exception.SDKInvalidInputFormat(msg)

        if WWPNS not in connection_info.keys():
            raise exception.SDKInvalidInputFormat("WWPNS are not passed in!")

        if not isinstance(connection_info[WWPNS], list):
            msg = ("wwpns in connection info must be of type list, however "
                   "the object passed in is: %s !" % connection_info[WWPNS])
            raise exception.SDKInvalidInputFormat(msg)

        for i in range(len(connection_info[FCPS])):
            connection_info[FCPS][i] = connection_info[FCPS][i].lower()
        for fcp in connection_info[FCPS]:
            self._validate_fcp(fcp)

        for i in range(len(connection_info[WWPNS])):
            connection_info[WWPNS][i] = connection_info[WWPNS][i].lower()
        for wwpn in connection_info[WWPNS]:
            if not self._is_16bit_hex(wwpn):
                msg = ("WWPN value: %s is illegal!" % wwpn)
                raise exception.SDKInvalidInputFormat(msg)

    def _validate_fcp(self, fcp):
        # exclusively entering from _validate_fc_connection_info at this
        # moment, so will not check fcp object again. Modify it if necessary
        # in the future
        pattern = '^[0-9a-f]{1,4}$'
        try:
            if not re.match(pattern, fcp):
                raise exception.SDKInvalidInputFormat(
                    "fcp value: %s is illegal!" % fcp)
        except Exception:
            msg = ("fcp object must be of type string, "
                   "however the object passed in is: %s !" % fcp)
            raise exception.SDKInvalidInputFormat(msg)

    def _get_configurator(self, instance):
        # all input object should have been validated by _validate_xxx method
        # before being passed in
        if re.match(self._PATTERN_RHEL7, instance[OS_TYPE]):
            return _Configurator_RHEL7()
        elif re.match(self._PATTERN_SLES12, instance[OS_TYPE]):
            return _Configurator_SLES12()
        elif re.match(self._PATTERN_UBUNTU16, instance[OS_TYPE]):
            return _Configurator_Ubuntu16()
        else:
            raise exception.SDKInvalidInputFormat(
                "unknown instance os: %s!" % instance[OS_TYPE])
