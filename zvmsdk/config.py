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


import ConfigParser
import os


config_dicts_default = {
    'xcat': {
        'server': {"required": True},
        'username': {"type": None, "required": True},
        'password': {"default": None, "required": True},
        'master_node': {},
        'zhcp_node': {},
        'zhcp': {"default": None, "type": None, "required": True},
        'ca_file': {},
        'connection_timeout': {"default": 3600, "type": int},
    },
    'logging': {
        'log_file': {"default": "zvmsdk.log"},
        'log_level': {"default": "logging.INFO"},
    },
    'zvm': {
        'host': {"required": True},
        'default_nic_vdev': {"default": '1000'},
        'user_default_password': {"default": 'dfltpass'},
        'diskpool': {"required": True},
        'user_root_vdev': {"default": '0100'},
        'root_disk_units': {"default": '3338'},
        'diskpool_type': {"default": 'ECKD'},
        'client_type': {"default": 'xcat'},
    },
    'network': {
        'my_ip': {},
        'device': {},
        'broadcast_v4': {},
        'gateway_v4': {},
        'netmask_v4': {},
        'subchannels': {},
        'nic_name': {},
    },
    'instance': {
        'instances_path': {},
        'tempdir': {},
        'reachable_timeout': {"default": 300, "type": 'int'},
    }
}


class ConfigOpts(object):

    def __init__(self):
        self.dicts = {}

    def register(self):
        cf = ConfigParser.ConfigParser()
        read_file = self.find_config_file(project="zvmsdk")
        cf.read(read_file)
        # return all sections in a list
        secs = cf.sections()
        config_dicts_override = self.config_ini_to_dicts(secs, cf)
        try:
            configs = self.merge(config_dicts_default, config_dicts_override)
        except ImportError:
            pass
        con = self._config_fill_option(configs)
        con = self.toDict(con)
        self._check_required(con)
        self._check_type(con)

        for k1, v1 in con.items():
            r_con = {}
            for k2, v2 in v1.items():
                r_con[k2] = v2.default
            con[k1] = r_con
        # the format of conf : xCAT:{'server':xxx,'username':xxx}
        # call method :CONF.group.option   e.g: CONF.xCAT.zvm_xcat_server
        con = self.toDict(con)
        return con

    def _check_required(self, conf):
        '''Check that all opts marked as required have values specified.
        raises: RequiredOptError
        the format of conf:
        xat:{
            'zvm_xcat_server':{"default":xx,"type":int,"required":true}
            }
        '''
        for k1, v1 in conf.items():
            for k2, v2 in v1.items():
                if v2.required and (v2.default is None):
                    raise RequiredOptMissingError(k1, k2)

    def _check_type(self, conf):
        '''
        the format of conf:
        xat:{
            'zvm_xcat_server':{"default":xx,"type":int,"required":true}
            }
        '''
        for v1 in conf.values():
            for k2, v2 in v1.items():
                if v2.type is 'int':
                    v2.default = int(v2.default)

    def _config_fill_option(self, conf):
        '''
        :param conf:
        xat:{
            'zvm_xcat_server':{"default":xx,"type":int,"required":true}
            }
        :return conf:
        xat:{
            'zvm_xcat_server':{"default":xx,"type":int,"required":true}
            }
        '''
        for k, v in conf.items():
            confs = {}
            for dk, dv in v.items():
                # the format of dk,dv:
                # 'zvm_xcat_server':{"default":xx,"type":int,"required":true}
                #     'zvm_xcat_server':{}
                #     'zvm_xcat_server':xx,
                # }
                if isinstance(dv, dict):
                    dv.setdefault('type', None)
                    dv.setdefault('required', False)
                    dv.setdefault('default', None)
                    confs[dk] = dv
                else:
                    dv = {}
                    dv['type'] = None
                    dv['required'] = False
                    dv['default'] = v[dk]
                    confs[dk] = dv
            conf[k] = confs
        return conf

    def config_ini_to_dicts(self, secs, cf):
        for sec in secs:
            self.dicts[sec] = {}
            # get all options of the section in a list
            opts = cf.options(sec)
            for opt in opts:
                val = cf.get(sec, opt)
                self.dicts[sec][opt] = val
        return self.dicts

    def merge(self, defaults, override):
        '''
        param defaults:
        'xcat':{
            'zvm_xcat_server':{"default":None,"type":None,"required":false}
            }
        param override:
        'xcat':{
            'zvm_xcat_server':None,
            }
        returns r: is a dict and the format is same as
        the parameter 'default' or 'override'
        '''
        r = {}
        for k, v in defaults.items():
            if k in override:
                if isinstance(v, dict) and isinstance(override[k], dict):
                    r[k] = self.merge(v, override[k])
                elif isinstance(v, dict):
                    if override[k] is not None:
                        v['default'] = override[k]
                    r[k] = v
                else:
                    r[k] = override[k]
            else:
                r[k] = v

        for k, v in override.items():
            if k not in defaults:
                r[k] = v
        return r

    def toDict(self, d):
        D = Dict()
        for k, v in d.items():
            D[k] = self.toDict(v) if isinstance(v, dict) else v
        return D

    def _fixpath(self, p):
        """Apply tilde expansion and absolutization to a path."""
        return os.path.abspath(os.path.expanduser(p))

    def _get_config_dirs(self):
        """Return a list of directories where config files may be located.

        following directories are returned::

          ./
          ../etc
          ~/
          /etc/zvmsdk/
        """
        _cwd = os.path.split(os.path.abspath(__file__))[0]
        _pdir = os.path.split(_cwd)[0]
        _etcdir = ''.join((_pdir, '/', 'etc/'))
        cfg_dirs = [
            self._fixpath(_cwd),
            self._fixpath(_etcdir),
            self._fixpath('~'),
            self._fixpath('/etc/zvmsdk/')
        ]
        return [x for x in cfg_dirs if x]

    def _search_dirs(self, dirs, basename, extension=""):
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

    def find_config_file(self, project=None, extension='.conf'):
        """Return the config file.

        :param project: "zvmsdk"
        :param extension: the type of the config file

        """

        cfg_dirs = self._get_config_dirs()
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


class RequiredOptMissingError(Exception):
    """Raised if an option is required but no value is supplied by the user."""

    def __init__(self, grp_name, opt_name):
        self.grp_name = grp_name
        self.opt_name = opt_name

    def __str__(self):
        return "value required for option %s - %s" % (self.grp_name,
                                                      self.opt_name)


CONF = ConfigOpts()
CONF = CONF.register()
