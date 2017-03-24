#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import config_default
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

class ConfigOpts(object):
    int_type = ('zvm_reachable_timeout', 'zvm_xcat_connection_timeout', 'zvm_console_log_size',
                      'xcat_free_space_threshold', 'xcat_image_clean_period', 'default_config_dirs')
    def __init__(self):
        self.dicts={}
    
    def register(self):
        cf = ConfigParser.ConfigParser()
        read_file = self.find_config_file(project="zvmsdk")
        cf.read(read_file)
        # return all sections in a list
        secs = cf.sections()
        config_dicts_override=self.config_dicts_func(secs,cf)
        try:
            configs = self.merge(config_default.configs, config_dicts_override)
        except ImportError:
            pass
        con={}
        for v in configs.values():
            for dk,dv in v.items():
                con[dk]=dv
        con=self.toDict(con)
        return con

    def config_dicts_func(self,secs,cf):
        for sec in secs:
            self.dicts[sec]={}
            # get all options of the section in a list
            opts=cf.options(sec)
            for opt in opts:
                # type 
                if opt in self.int_type:
                    val=cf.getint(sec,opt)
                else:
                    val=cf.get(sec,opt)
                self.dicts[sec][opt]=val
        return self.dicts

    def merge(self,defaults, override):
        r = {}
        for k, v in defaults.items():
            if k in override:
                if isinstance(v, dict):
                    r[k] = self.merge(v, override[k])
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



CONF = ConfigOpts()
CONF=CONF.register()