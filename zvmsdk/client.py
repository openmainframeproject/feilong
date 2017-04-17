#!/usr/bin/env python
# -*- coding: utf-8 -*-
import interface

_GET_MANAGER = None


class ZVMClient(object):
    """
    InterfaceManager manage different Interfaces who connect to ZVM
    """
    def __init__(self, interface_type):
        # one way
        self.manager = interface.InterfaceManager()
        self.interface = self.manager.get_interface(interface_type)
        # another way
        # self.interface = self._get_interface(interface_type)

    def create_request(self, func_name=None, **kws):
        self.interface.request(func_name, kws)

    def get_interface(self, interface_type):
        if interface_type == 'xcat':
            return interface.LibXcatInterface()
        elif interface_type == 'Libvirt':
            return interface.LibvirtInterface()
        else:
            # ERROR
            pass


def get_client():
    # use the default interface type in configuration file
    global _GET_MANAGER

    if _GET_MANAGER is not None:
        return _GET_MANAGER

    _GET_MANAGER = ZVMClient(CONF.interface_type)
    return _GET_MANAGER
