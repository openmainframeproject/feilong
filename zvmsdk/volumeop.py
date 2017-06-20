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


import re

from log import LOG
from exception import ZVMVolumeError


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

    def attach_volume_to_instance(self, instance, volume, connection_info,
                                  is_rollback_on_failure=False):
        raise NotImplementedError

    def detach_volume_from_instance(self, instance, volume, connection_info,
                                    is_rollback_on_failure=False):
        raise NotImplementedError


class VolumeConfiguratorAPI(object):
    """Volume configure APIs to implement volume config jobs on the
    target instance, like: attach, detach, and so on.

    The reason to design these APIs is to hide the details among
    different Linux distributions and releases.
    """

    def config_attach(self, instance, volume, connection_info):
        raise NotImplementedError

    def config_detach(self, instance, volume, connection_info):
        raise NotImplementedError


class Configurator_RHEL7(VolumeConfiguratorAPI):

    def config_attach(self, instance, volume, connection_info):
        pass

    def config_detach(self, instance, volume, connection_info):
        pass


class Configurator_SLES12(VolumeConfiguratorAPI):

    def config_attach(self, instance, volume, connection_info):
        pass

    def config_detach(self, instance, volume, connection_info):
        pass


class Configurator_Ubuntu16(VolumeConfiguratorAPI):

    def config_attach(self, instance, volume, connection_info):
        pass

    def config_detach(self, instance, volume, connection_info):
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

    def attach_volume_to_instance(self, instance, volume, connection_info,
                                  is_rollback_on_failure=False):
        LOG.debug("Enter VolumeOperator.attach_volume_to_instance, attach "
                  "volume %(vol)s to instance %(inst)s by connection_info "
                  "%(conn_info)s.")

        self._validate_instance(instance)
        self._validate_volume(volume)
        self._validate_connection_info(connection_info)

        configurator = self._get_configurator(instance)
        configurator.config_attach(instance, volume, connection_info)

        LOG.debug("Exit VolumeOperator.attach_volume_to_instance.")

    def detach_volume_from_instance(self, instance, volume, connection_info,
                                    is_rollback_on_failure=False):
        pass

    def _validate_instance(self, instance):
        if not instance:
            raise ZVMVolumeError("instance object is not passed in!")

        if not isinstance(instance, dict):
            msg = ("instance object must be of type dict, however the object "
                   "passed in is: %s !" % instance)
            raise ZVMVolumeError(msg)

        if 'os_type' not in instance.keys():
            raise ZVMVolumeError("instance os_type is not passed in!")

        if 'name' not in instance.keys():
            raise ZVMVolumeError("instance name is not passed in!")

        # os_type patterns for rhel7, sles12 and ubuntu 16, i.e.
        # rhel7: rhel7, rhel7.2
        # sles12: sles12, sles12sp2
        # ubuntu16: ubuntu16, ubuntu16.04
        os_type_pattern = (self._PATTERN_RHEL7 +
                           '|' + self._PATTERN_SLES12 +
                           '|' + self._PATTERN_UBUNTU16)
        if not re.match(os_type_pattern, instance['os_type']):
            msg = ("unknown instance os_type: %s . It must be one of set "
                   "'rhel7, sles12, or ubuntu16'." % instance['os_type'])
            raise ZVMVolumeError(msg)

    def _is_16bit_hex(self, value):
        pattern = '^[0-9a-f]{16}$'
        try:
            return re.match(pattern, value)
        except:
            return False

    def _validate_volume(self, volume):
        if not volume:
            raise ZVMVolumeError("volume object is not passed in!")

        if not isinstance(volume, dict):
            msg = ("volume object must be of type dict, however the object "
                   "passed in is: %s !" % volume)
            raise ZVMVolumeError(msg)

        if 'type' not in volume.keys():
            raise ZVMVolumeError("volume type is not passed in!")

        # support only FiberChannel volumes at this moment
        if volume['type'] != 'fc':
            msg = ("volume type: %s is illegal!" % volume['type'])
            raise ZVMVolumeError(msg)
        self._validate_fc_volume(volume)

    def _validate_fc_volume(self, volume):
        # exclusively entering from _validate_volume at this moment, so will
        # not check volume object again. Modify it if necessary in the future
        if 'lun' not in volume.keys():
            raise ZVMVolumeError("volume LUN is not passed in!")

        volume['lun'] = volume['lun'].lower()
        if not self._is_16bit_hex(volume['lun']):
            msg = ("volume LUN value: %s is illegal!" % volume['lun'])
            raise ZVMVolumeError(msg)

    def _validate_connection_info(self, connection_info):
        if not connection_info:
            raise ZVMVolumeError("connection info is not passed in!")

        if not isinstance(connection_info, dict):
            msg = ("connection info must be of type dict, however the object "
                   "passed in is: %s !" % connection_info)
            raise ZVMVolumeError(msg)

        if 'protocol' not in connection_info.keys():
            raise ZVMVolumeError("connection protocol is not passed in!")

        # support only FiberChannel volumes at this moment
        if connection_info['protocol'] != 'fc':
            raise ZVMVolumeError("connection protocol: %s is illegal!"
                                 % connection_info['protocol'])
        self._validate_fc_connection_info(connection_info)

    def _validate_fc_connection_info(self, connection_info):
        # exclusively entering from _validate_connection_info at this moment,
        # so will not check connection_info object again. Modify it if
        # necessary in the future
        if 'fcps' not in connection_info.keys():
            raise ZVMVolumeError("fcp devices are not passed in!")

        if not isinstance(connection_info['fcps'], list):
            msg = ("fcp devices in connection info must be of type dict, "
                   "however the object passed in is: %s !"
                   % connection_info['fcps'])
            raise ZVMVolumeError(msg)

        if 'wwpns' not in connection_info.keys():
            raise ZVMVolumeError("WWPNS are not passed in!")

        if not isinstance(connection_info['wwpns'], list):
            msg = ("wwpns in connection info must be of type dict, however "
                   "the object passed in is: %s !" % connection_info['wwpns'])
            raise ZVMVolumeError(msg)

        for i in range(len(connection_info['fcps'])):
            connection_info['fcps'][i] = connection_info['fcps'][i].lower()
        for fcp in connection_info['fcps']:
            self._validate_fcp(fcp)

        for i in range(len(connection_info['wwpns'])):
            connection_info['wwpns'][i] = connection_info['wwpns'][i].lower()
        for wwpn in connection_info['wwpns']:
            if not self._is_16bit_hex(wwpn):
                msg = ("WWPN value: %s is illegal!" % wwpn)
                raise ZVMVolumeError(msg)

    def _validate_fcp(self, fcp):
        # exclusively entering from _validate_fc_connection_info at this
        # moment, so will not check fcp object again. Modify it if necessary
        # in the future
        pattern = '^[0-9a-f]{1,4}$'
        try:
            if not re.match(pattern, fcp):
                raise ZVMVolumeError("fcp value: %s is illegal!" % fcp)
        except:
            msg = ("fcp object must be of type string, "
                   "however the object passed in is: %s !" % fcp)
            raise ZVMVolumeError(msg)

    def _get_configurator(self, instance):
        # all input object should have been validated by _validate_xxx method
        # before being passed in
        if re.match(self._PATTERN_RHEL7, instance['os_type']):
            return Configurator_RHEL7()
        elif re.match(self._PATTERN_SLES12, instance['os_type']):
            return Configurator_SLES12()
        elif re.match(self._PATTERN_UBUNTU16, instance['os_type']):
            return Configurator_Ubuntu16()
        else:
            raise ZVMVolumeError("unknown instance os: %s!"
                                 % instance['os_type'])
