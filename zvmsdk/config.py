

import ConfigParser
import os


config_dicts_default = {
    'xCAT': {
        'zvm_xcat_server': {"required": True},
        'zvm_xcat_username': {"type": None, "required": True},
        'zvm_xcat_password': {"default": None, "required": True},
        'zvm_xcat_master': {},
        'zvm_zhcp_node': {},
        'zhcp': {"default": None, "type": None, "required": True},
    },
    'logging': {
        'LOG_FILE': {"default": "zvmsdk.log"},
        'LOG_LEVEL': {"default": "logging.INFO"},
    },
    'zVM': {
        'zvm_host': {},
        'zvm_default_nic_vdev': {"default": '1000'},
        'zvm_user_default_password': {"default": 'dfltpass'},
        'zvm_diskpool': {"default": 'diskpoolname'},
        'zvm_user_root_vdev': {"default": '0100'},
        'root_disk_units': {"default": '3338'},
        'zvm_diskpool_type': {"default": 'ECKD'},
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
    'Volume': {
        'volume_mgr_userid': {},
        'volume_mgr_node': {},
        'volume_diskpool': {},
        'volume_filesystem': {},
        'volume_vdev_start': {},
    },
    'instance': {
        'instances_path': {},
        'tempdir': {},
        'zvm_reachable_timeout': {"default": 300, "type": 'int'},
    }
}


class ConfigOpts(object):

    def __init__(self):
        self.dicts = {}
        self.confs = {}

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
        conf_fill = self._config_fill_option(configs)
        con = self.toDict(conf_fill)
        self._check_required(con)
        self._check_type(con)

        r_con = {}
        for k, v in con.items():
            r_con[k] = v.default
        r_con = self.toDict(r_con)
        return r_con

    def _check_required(self, conf):
        '''Check that all opts marked as required have values specified.
        raises: RequiredOptError
        '''
        for k, v in conf.items():
            if v.required and (v.default is None):
                raise RequiredOptError(k)

    def _check_type(self, conf):
        for k, v in conf.items():
            if v.type is 'int':
                v.default = int(v.default)

    def _config_fill_option(self, conf):
        for v in conf.values():
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
                    self.confs[dk] = dv
                else:
                    dv = {}
                    dv['type'] = None
                    dv['required'] = False
                    dv['default'] = v[dk]
                    self.confs[dk] = dv
        return self.confs

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
        'xCAT':{
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


class RequiredOptError(Exception):
    """Raised if an option is required but no value is supplied by the user."""

    def __init__(self, opt_name):
        self.opt_name = opt_name

    def __str__(self):
        return "value required for option %s" % (self.opt_name)


CONF = ConfigOpts()
CONF = CONF.register()
