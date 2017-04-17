#!/usr/bin/env python
# -*- coding: utf-8 -*-

from zvmsdk import config
from zvmsdk import log
import constants as const
from zvmsdk import utils as zvmutils

CONF = config.CONF
LOG = log.LOG


class Interface(object):
    """
    xcat and libvirt both have these functions,and parm are same.
    e.g: create_userid_request
    already exist in utils.py
    """

    def common_function(self):
        # it's the common function for libxcat and libvirt
        pass

    def request(self, func_name, **kws):
        pass


class XcatInterface(Interface):
    """
    These functions are only for xcat
    already exist in utils.py
    """

    def request(self, func_name, **kws):
        return getattr(self, func_name)()

    def _get_xcat_url(self):
        pass

    def _xcat_request(self, method, url, body):
        pass

    def create_userid_request(self, **kws):
        if 'instance_name' not in kws:
            raise RequiredOptError('instance_name')
        if 'cpu' not in kws:
            raise RequiredOptError('cpu')
        if 'memory' not in kws:
            raise RequiredOptError('memory')
        if 'imagename' not in kws:
            raise RequiredOptError('imagename')

        url = self._get_xcat_url().mkvm('/' + kws['instance_name'])
        kwprofile = 'profile=%s' % const.ZVM_USER_PROFILE
        body = [kwprofile,
                'password=%s' % CONF.zvm_user_default_password,
                'cpu=%i' % kws['cpu'],
                'memory=%im' % kws['memory'],
                'privilege=%s' % const.ZVM_USER_DEFAULT_PRIVILEGE,
                'ipl=%s' % CONF.zvm_user_root_vdev,
                'imagename=%s' % kws['image_name']]
        return self._xcat_request("POST", url, body)

    def create_xcat_table_about_nic(self, **kws):
        if 'instance_name' not in kws:
            raise RequiredOptError('instance_name')
        if 'ip_addr' not in kws:
            raise RequiredOptError('ip_addr')
        nic_vdev = CONF.zvm_default_nic_vdev
        nic_name = CONF.nic_name
        zhcpnode = CONF.zhcp
        # zvmutils._delete_xcat_mac(kws['instance_name'])
        zvmutils.add_xcat_mac(kws['instance_name'], nic_vdev, kws['ip_addr'],
                              zhcpnode)
        zvmutils.add_xcat_switch(kws['instance_name'], nic_name, nic_vdev,
                                 zhcpnode)


class LibvirtInterface(Interface):
    # these functions are only for libvirt
    def libvirt_request(self):
        pass


class InterfaceManager(object):
    """
    manager manages different interfaces
    it is a interface factory
    """

    def __init__(self):
        self.interface = Interface()

    def get_interface(self, interface_type):
        if interface_type == 'Libxcat':
            self.interface = XcatInterface()
            return self.interface
        elif interface_type == 'Libvirt':
            self.interface = LibvirtInterface()
            return self.interface
        else:
            raise Exception(r"the interface_type is not exist'%s'" %
                            interface_type)


class RequiredOptError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "value required for option %s" % self.name
