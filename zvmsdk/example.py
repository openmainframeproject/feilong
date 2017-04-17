"""
    HOW TO USE ZVM CLIENT
    example:"create_userid" and "_add_nic_to_table"
            implemented through ZVM CLIENT
"""
# !/usr/bin/env python
# -*- coding: utf-8 -*-

import client as zvmclient
from zvmsdk import config
from zvmsdk import log
from zvmsdk import utils as zvmutils

CONF = config.CONF
LOG = log.LOG


def create_userid(self, instance_name, cpu, memory, image_name):
    """
    Create z/VM userid into user directory for a z/VM instance.
    """
    LOG.debug("Creating the z/VM user entry for instance %s"
              % instance_name)

    # step1-1: create a object:client, which use the default interface
    # in configureation files
    client = zvmclient.get_client()

    # or we can assign a interface type
    # step1-2:another way  if we don't use the type in CONF
    # client = zvmclient.ZVMClient('libvirt')

    try:
        # step2: call "request" method to interact with ZVM
        result = client.create_request(func_name='create_userid_request',
                                       instance_name=instance_name,
                                       cpu=cpu,
                                       memory=memory,
                                       image_name=image_name)

        # step3: process the returned result
        if result is True:
            # success
            pass
        else:
            # failure
            pass

        size = CONF.root_disk_units
        # Add root disk and set ipl
        self.add_mdisk(instance_name, CONF.zvm_diskpool,
                       CONF.zvm_user_root_vdev, size)
        self.set_ipl(instance_name, CONF.zvm_user_root_vdev)

    except Exception as err:
        msg = ("Failed to create z/VM userid: %s" % err)
        LOG.error(msg)
        raise zvmutils.ZVMException(msg=err)
