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

from zvmsdk.exception import ZVMVolumeError
from zvmsdk.log import LOG


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

    def __init__(self, instance, volume, connection_info):
        self.instance = instance
        self.volume = volume
        self.connection_info = connection_info

    def config_attach(self, is_rollback_on_failure=False):
        raise NotImplementedError

    def config_detach(self, is_rollback_on_failure=False):
        raise NotImplementedError


class Configurator_RHEL7(VolumeConfiguratorAPI):

    def config_attach(self, is_rollback_on_failure=False):
        pass

    def config_detach(self, is_rollback_on_failure=False):
        pass


class Configurator_SLES12(VolumeConfiguratorAPI):

    def config_attach(self, is_rollback_on_failure=False):
        pass

    def config_detach(self, is_rollback_on_failure=False):
        pass


class Configurator_Ubuntu16(VolumeConfiguratorAPI):

    def config_attach(self, is_rollback_on_failure=False):
        pass

    def config_detach(self, is_rollback_on_failure=False):
        pass


class VolumeOperator(VolumeOperatorAPI):

    __singleton = None

    __PATTERN_RHEL7 = '^rhel7(\.[0-9])?$'
    __PATTERN_SLES12 = '^sles12(sp[1-9])?$'
    __PATTERN_UBUNTU16 = '^ubuntu16(\.[0-9][0-9])?$'

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

        configurator = self._get_configurator(instance, volume,
                                              connection_info)
        configurator.config_attach(is_rollback_on_failure)

        LOG.debug("Exit VolumeOperator.attach_volume_to_instance.")

    def detach_volume_from_instance(self, instance, volume, connection_info,
                                    is_rollback_on_failure=False):
        pass

    def _validate_instance(self, instance):
        if not instance:
            raise ZVMVolumeError("instance object is not passed in!")

        if not isinstance(instance, dict):
            raise ZVMVolumeError("instance object must be of type dict!")

        if 'os_type' not in instance.keys():
            raise ZVMVolumeError("instance os_type is not passed in!")

        if 'name' not in instance.keys():
            raise ZVMVolumeError("instance name is not passed in!")

        # os_type patterns for rhel7, sles12 and ubuntu 16, i.e.
        # rhel7: rhel7, rhel7.2
        # sles12: sles12, sles12sp2
        # ubuntu16: ubuntu16, ubuntu16.04
        OS_TYPE_PATTERN = (self.__PATTERN_RHEL7 +
                           '|' + self.__PATTERN_SLES12 +
                           '|' + self.__PATTERN_UBUNTU16)
        if not re.match(OS_TYPE_PATTERN, instance['os_type']):
            msg = ("unknown instance os_type: %s . It must be one of set "
                   "'rhel7, sles12, or ubuntu16'." % instance['os_type'])
            raise ZVMVolumeError(msg)

    def _get_configurator(self, instance, volume, connection_info):
        pass
