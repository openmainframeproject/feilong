#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import collections
import copy
import errno
import functools
import glob
import itertools
import logging
import os
import string
import sys

config_dicts_default = {
    'xCAT':{
        'zvm_xcat_server':{"default":None,"type":None,"required":"ture"},
        'zvm_xcat_username':{"default":None,"type":None,"required":"ture"},
        'zvm_xcat_password':{"default":None,"type":None,"required":"ture"},
        'zvm_xcat_master':{"default":None,"type":None,"required":"ture"},
        'zvm_zhcp_node':{"default":None,"type":None,"required":"ture"},
        'zhcp':{"default":None,"type":None,"required":"ture"},
    },
    'logging':{
        'LOG_FILE':{"default":"zvmsdk.log","type":None,"required":"false"},
        'LOG_LEVEL':{"default":"logging.INFO","type":None,"required":"false"},
    },
    'zVM':{
        'zvm_host':{"default":None,"type":None,"required":"false"},
        'zvm_default_nic_vdev':{"default":'1000',"type":None,"required":"false"},
        'zvm_user_default_password':'dfltpass',
        'zvm_diskpool':{"default":None,"type":None,"required":"false"},
        'zvm_user_root_vdev':{"default":'0100',"type":None,"required":"false"},
        'root_disk_units':{"default":'3338',"type":None,"required":"false"},
        'zvm_diskpool_type':{"default":'ECKD',"type":None,"required":"false"},
    },
    'network':{
        'my_ip':{"default":None,"type":None,"required":"false"},
        'device':{"default":None,"type":None,"required":"false"},
        'broadcast_v4':{"default":None,"type":None,"required":"false"},
        'gateway_v4':{"default":None,"type":None,"required":"false"},
        'netmask_v4':{"default":None,"type":None,"required":"false"},
        'subchannels':{"default":None,"type":None,"required":"false"},
        'nic_name':{"default":None,"type":None,"required":"false"},
    },
    'Volume':{
        'volume_mgr_userid':{"default":None,"type":None,"required":"false"},
        'volume_mgr_node':{"default":None,"type":None,"required":"false"},
        'volume_diskpool':{"default":None,"type":None,"required":"false"},
        'volume_filesystem':{"default":None,"type":None,"required":"false"},
        'volume_vdev_start':{"default":None,"type":None,"required":"false"},
    },
    'instance':{
        'instances_path':{"default":None,"type":None,"required":"false"},
        'tempdir':{"default":None,"type":None,"required":"false"},
        'zvm_reachable_timeout':{"default":300,"type":'int',"required":"false"},
    }
}
class ConfigOpts(object):

    def __init__(self):
        self.dicts={}
        self.conf={}
    
    def register(self):
        cf = ConfigParser.ConfigParser()
        read_file = self.find_config_file(project="zvmsdk")
        cf.read(read_file)
        # return all sections in a list
        secs = cf.sections()
        config_dicts_override=self.config_dicts_func(secs,cf)
        try:
            
            configs = self.merge(config_dicts_default, config_dicts_override)
        except ImportError:
            pass
        
        con={}
        for v in configs.values():
            for dk,dv in v.items():
                if isinstance(dv,dict):
                    self.conf[dk]=dv
                else:
                    dv={}
                    dv['type']=None
                    dv['required']="false"
                    dv['default']=v[dk]
                    self.conf[dk]=dv

        con=self.toDict(self.conf)
        self._check_required(con)
        self._check_type(con)

        r_con={}
        for k,v in con.items():
            r_con[k]=v.default
        r_con=self.toDict(r_con)
        return r_con

    def _check_required(self,conf):
        '''Check that all opts marked as required have values specified.
        raises: RequiredOptError
        '''
        for k,v in conf.items():
            if v.required and v.default is None:
                raise RequiredOptError(k)

    def _check_type(self,conf):
        for k,v in conf.items():
            if v.type is 'int':
                v.default=int(v.default)

    def config_dicts_func(self,secs,cf):
        for sec in secs:
            self.dicts[sec]={}
            # get all options of the section in a list
            opts=cf.options(sec)
            for opt in opts:
                val=cf.get(sec,opt)
                self.dicts[sec][opt]=val
        return self.dicts

    def merge(self,defaults, override):
        '''
        param defaults: 'xcat':{
                        'zvm_xcat_server':{"default":None,"type":None,"required":false}
                        }
        param override:  'xCAT':{
                         'zvm_xcat_server':None,
                         }

        returns r is a dict and the format is same as the parameter 'default'
 
        ''' 
        r = {}
        for k, v in defaults.items():
            if k in override:
                if isinstance(v, dict) and isinstance(override[k],dict):
                    r[k] = self.merge(v, override[k])
                elif isinstance(v,dict):
                    v['default']=override[k]
                    r[k]=v
                else:
                    r[k] = override[k]
            else:
                r[k] = v

        for k, v in override.items():
            if k not in defaults:
                r[k] = v
        return r

    def toDict(self,d):
        D = Dict()
        for k, v in d.items():
            D[k] = self.toDict(v) if isinstance(v, dict) else v
        return D

    def _fixpath(self,p):
        """Apply tilde expansion and absolutization to a path."""
        return os.path.abspath(os.path.expanduser(p))


    def _get_config_dirs(self,project=None):
        """Return a list of directories where config files may be located.

        following directories are returned::

          ./
          ~/
          nova/
        """
        cfg_dirs = [
            self._fixpath('./'),
            self._fixpath('~'),
            # '/nova'
        ]
        return [x for x in cfg_dirs if x]


    def _search_dirs(self,dirs, basename, extension=""):
        """Search a list of directories for a given filename or directory name.

        Iterator over the supplied directories, returning the first file
        found with the supplied name and extension.

        :param dirs: a list of directories
        :param basename: the filename
        :param extension: the file extension, for example '.conf'
        :returns: the path to a matching file, or None
        """
        for d in dirs:
            path = os.path.join(d, '%s%s' % (basename, extension))
            if os.path.exists(path):
                return path


    def find_config_file(self,project=None, extension='.conf'):
        """Return the config file.

        :param project: zvmsdk
        :param extension: the type of the config file

        """

        cfg_dirs = self._get_config_dirs(project)
        config_files = self._search_dirs(cfg_dirs, project, extension)

        return config_files
 


class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'CONF' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


class RequiredOptError(Exception):
    """Raised if an option is required but no value is supplied by the user."""

    def __init__(self, opt_name):
        self.opt_name = opt_name

    def __str__(self):
        return "value required for option %s" % (self.opt_name)

CONF = ConfigOpts()
CONF=CONF.register()
