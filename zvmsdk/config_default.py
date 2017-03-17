#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
configs = {
    'xCAT':{
        'zvm_xcat_server':None,
        'zvm_xcat_username':None,
        'zvm_xcat_password':None,
        'zvm_xcat_master':None,
        'zvm_zhcp_node':None,
        'zhcp':None
    },
    'logging':{
        'LOG_FILE':zvmsdk.log,
        'LOG_LEVEL':logging.INFO
    },
    'zVM':{
        'zvm_host':None,
        'zvm_default_nic_vdev':'1000',
        'zvm_user_default_password':'dfltpass',
        'zvm_diskpool':None,
        'zvm_user_root_vdev':'0100',
        'root_disk_units':'3338',
        'zvm_diskpool_type':'ECKD'
    },
    'network':{
        'my_ip':None,
        'device':None,
        'broadcast_v4':None,
        'gateway_v4':None,
        'netmask_v4':None,
        'subchannels':None,
        'nic_name':None
    },
    'Volume':{
        'volume_mgr_userid':None,
        'volume_mgr_node':None,
        'volume_diskpool':None,
        'volume_filesystem':None,
        'volume_vdev_start':None
    },
    'instance':{
        'instances_path':None,
        'tempdir':None,
        'zvm_reachable_timeout':300
    }
}