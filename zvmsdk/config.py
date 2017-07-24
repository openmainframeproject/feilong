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


class ZVMSDKConfigFileNotFound(Exception):
    """Config file not found exception."""
    def __init__(self, message):
        self.message = message
        super(ZVMSDKConfigFileNotFound, self).__init__(message)


class Opt(object):
    def __init__(self, opt_name, descritpion='', section='default',
                 opt_type='str', default=None, required=False):
        self.name = opt_name
        self.decsription = descritpion
        self.section = section
        self.opt_type = opt_type
        self.default = default
        self.required = required


zvm_opts = [
    # xcat options
    Opt('server',
        section='xcat',
        required=True),
    Opt('username',
        section='xcat',
        required=True),
    Opt('password',
        section='xcat',
        required=True),
    Opt('master_node',
        section='xcat',
        required=True),
    Opt('zhcp',
        section='xcat',
        required=True),
    Opt('ca_file',
        section='xcat'),
    Opt('connection_timeout',
        section='xcat',
        default=3600,
        opt_type='int'),
    Opt('free_space_threshold',
        section='xcat',
        default=50,
        opt_type='int'),
    Opt('mgt_ip',
        section='xcat',
        default=None),
    Opt('mgt_mask',
        section='xcat',
        default=None),
    # logging options
    Opt('log_file',
        section='logging',
        default='/tmp/zvmsdk.log'),
    Opt('log_level',
        section='logging',
        default='logging.INFO'),
    # zvm options
    Opt('host',
        section='zvm',
        required=True),
    Opt('default_nic_vdev',
        section='zvm',
        default='1000'),
    Opt('zvm_default_admin_userid',
        section='zvm'),
    Opt('user_default_password',
        section='zvm',
        required=True),
    Opt('disk_pool',
        section='zvm',
        required=True),
    Opt('user_profile',
        section='zvm'),
    Opt('user_root_vdev',
        section='zvm',
        default='0100'),
    Opt('client_type',
        section='zvm',
        default='xcat'),
    # image options
    Opt('temp_path',
        section='image',
        default='/tmp/zvmsdk/images/'),
    # network options
    Opt('my_ip',
        section='network',
        required=True),
    # guest options
    Opt('temp_path',
        section='guest',
        default='/tmp/zvmsdk/guests/'),
    Opt('reachable_timeout',
        section='guest',
        default=300,
        opt_type='int'),
    Opt('console_log_size',
        section='guest',
        default=100,
        opt_type='int'),
    # monitor options
    Opt('cache_interval',
        section='monitor',
        default=600,
        opt_type='int',
        ),
    # tests options
    Opt('image_path',
        section='tests',
        opt_type='str',
        ),
    Opt('image_os_version',
        section='tests',
        opt_type='str',
        ),
    Opt('userid_list',
        section='tests',
        opt_type='str',
        ),
    Opt('ip_addr_list',
        section='tests',
        opt_type='str',
        ),
    Opt('mac_user_prefix',
        section='tests',
        opt_type='str',
        ),
    Opt('vswitch',
        section='tests',
        opt_type='str',
        ),
    Opt('broadcast_v4',
        section='tests'),
    Opt('gateway_v4',
        section='tests'),
    Opt('netmask_v4',
        section='tests'),
    # SMUT options
    Opt('captureLogs',
        section='smut',
        default=False,
        opt_type='bool'),
    ]


class ConfigOpts(object):

    def __init__(self):
        self.dicts = {}

    def _get_config_dicts_default(self, opts):
        _dict = {}
        for opt in opts:
            sec = opt.section
            if _dict.get(sec) is None:
                _dict[sec] = {}
            _dict[sec][opt.name] = {'required': opt.required,
                                    'default': opt.default,
                                    'type': opt.opt_type}
        return _dict

    def register(self, opts):
        cf = ConfigParser.ConfigParser()
        read_file = self.find_config_file(project="zvmsdk")
        cf.read(read_file)
        # return all sections in a list
        secs = cf.sections()
        config_dicts_override = self.config_ini_to_dicts(secs, cf)

        config_dicts_default = self._get_config_dicts_default(opts)

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
                if v2.type == 'int':
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
            self._fixpath('/etc/zvmsdk/'),
            self._fixpath('/etc/'),
            self._fixpath('~'),
            self._fixpath(_etcdir),
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

        msg = "zvmsdk config file not found in %s" % str(dirs)
        raise ZVMSDKConfigFileNotFound(msg)

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
CONF = CONF.register(zvm_opts)
