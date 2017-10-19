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


import abc
import re
import six

from zvmsdk import config
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
