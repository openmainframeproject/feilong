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
    def __init__(self, opt_name, section='default',
                 opt_type='str', help='',
                 default='', required=False):
        self.name = opt_name
        self.section = section
        self.opt_type = opt_type
        self.default = default
        self.required = required
        self.help = help


zvm_opts = [
    # logging options
    Opt('log_dir',
        section='logging',
        default='/var/log/zvmsdk/',
        help='''
Directory where log file to be put into.

SDK has a set of logs to help administrator to debug
and aduit actions performed through SDK. Edit this option
if you want to put logs into specified place.

Please ensure the service running on the consume which
consumes SDK has the authorization to write to the path.
    '''),
    Opt('log_level',
        section='logging',
        default='logging.INFO',
        help='''
Level of the log.

SDK utilize python logging package to help admin debug
or analyze issues. it's recommend to set this value
to logging.DEBUG to get more detailed logs and set it to
logging.INFO(default) in normal situation.

recommend values:
logging.ERROR: level above ERROR will be written to log file.
logging.WARNINS: level above WARNING(ERROR, WARNING)
                 will be written to log file.
logging.INFO: level above INFO(ERROR, WARNING, INFO)
              will be written to log file.
logging.DEBUG: All log level (ERROR, WARNING, INFO, DEBUG)
               will be written to log file.
    '''),
    # zvm options
    Opt('default_nic_vdev',
        section='zvm',
        default='1000',
        help='''
Virtual device number for default NIC address.

This value is the first NIC virtual device number,
each NIC needs 3 numbers for control/read/write, so by default
the first NIC's address is 1000, the second one is 1003 etc.

Possible values:
    An integer value in hex format, between 0 and 65536 (x'FFFF').
    It should not conflict with other device numbers in the z/VM guest's
    configuration, for example device numbers of the root or ephemeral or
    persistent disks.

Sample NIC definitions in the z/VM user directory:
    NICDEF 1000 TYPE QDIO LAN SYSTEM <vswitch1> MACID <macid1>
    NICDEF 1003 TYPE QDIO LAN SYSTEM <vswitch2> MACID <macid2>
        '''
        ),
    Opt('default_admin_userid',
        section='zvm',
        help='''
Default LOGONBY userid(s) for the cloud.

This is a set of z/VM userid(s) which are allowed to logon using the LOGONBY
keyword to the guests created by the z/VM SDK solution, compatible with
the LBYONLY keyword of the user directory statement. This value is only used
when a guest is created. If you change this value, existing guests' directory
entries are not automatically updated with the new value.
When an ESM is installed, this parameter only governs when the ESM
defers to CP's processing.

Usage note:
    The default is an empty string (''). When the string is empty, you can't
    log on to your instances using the 3270 protocol; When a
    non-empty string is provided, blank chars will be used as delimiter,
    you can use LOGONBY xxx command to log on the
    OpenStack created guest using the corresponding admin userid's password.

    For example, when you set this value to 'oper1 oper2 oper3 jones', it means
    you can use any one of 'oper1', 'oper2', 'oper3', 'jones' as an admin user.

    see the z/VM CP Planning and Administration for additional information.

Possible values:
    A maximum of 8 blank-delimited strings. Each non-blank string must be a
    valid z/VM userid.
    e.g  '' is a valid value.
         'oper1 oper2' is a valid value.
         'o1 o2 o3 o4 o5 o6 o7 o8 o9' is NOT a valid value.
    '''),
    # FIXME: remove this option when switch to smut
    Opt('user_default_password',
        section='zvm'),
    Opt('disk_pool',
        section='zvm',
        required=True,
        help='''
zVM disk pool and type for root/ephemeral disks.

The option is combined by 2 parts and use : as separator.

First part is the volume group name from your directory manager
on your z/VM system, which will be used for ephemeral disks for
new guest. A dollar sign ($) is not allowed in the name.

Second part is type of the disk in the disk pool.
The disks in the disk pool must all be the same type (ECKD or FBA).
Possible values of the disk pool type:
    A string, either ECKD or FBA.

Sample configuration:
    diskpo1:ECKD
    testpool:FBA
    '''),
    Opt('user_profile',
        section='zvm',
        help='''
PROFILE name to use when creating a z/VM guest.

When SDK deploys an guest on z/VM, it can include some
common statements from a PROFILE definition.
This PROFILE must already be included in your z/VM user directory.

Possible values:
    An 8 character name of a PROFILE that is already defined in the z/VM
    user directory.
    '''),
    Opt('user_root_vdev',
        section='zvm',
        default='0100',
        help='''
Virtual device number for root disk.

When SDK deploys an guest, it creates a root disk and potentially
several data disks. This value is the virtual device number of the root
disk.

Possible values:
    An integer value in hex format, between 0 and 65536 (x'FFFF').
    It should not conflict with other device numbers in the z/VM guest's
    configuration, for example device numbers of the NICs or ephemeral or
    persistent disks.

Sample root disk in user directory:
    MDISK 0100 <disktype> <start> <end> <volumelabel> <readwrite>
'''),
    # image options
    Opt('temp_path',
        section='image',
        default='/tmp/zvmsdk/images/',
        help='''
Temp path to store image temp information.

During guest creation, image transferred from upper layer need to be
create some temp files, this option is used to tell SDK where
to store the temp files, make sure the process running SDK is able to
read write the directory.
    '''),
    # image options
    Opt('sdk_image_repository',
        section='image',
        default='/var/lib/zvmsdk/images',
        help='''
Directory to store sdk images.

SDK image repository to store the imported images and the staging images that
is in snapshotting. Once snapshot finished, the image will be removed to the
netboot directory accordingly. Two kinds of image repository looks like:
/var/lib/zvmsdk/images/netboot/<image_osversion>/<imagename>
/var/lib/zvmsdk/images/staging/<image_osversion>/<imagename>
    '''),
    # network options
    Opt('my_ip',
        section='network',
        required=True,
        help='''
IP address of the Linux machine which is running SDK on.

Some remote copy operations need to be performed during guest creation,
this option tell the SDK the host ip which can be used to perform copy
from and copy to operations.
    '''),
    # guest options
    Opt('temp_path',
        section='guest',
        default='/tmp/zvmsdk/guests/',
        help='''
Temp path to store guest temp information.

During guest creation, some temp data need to be stored in order to
be provided to guest later, this option is used to tell SDK where
to store the temp files, make sure the process running SDK is able to
read write the directory.
    '''),
    Opt('console_log_size',
        section='guest',
        default=100,
        opt_type='int',
        help='''
The maximum allowed console log size, in kilobytes.

Console logs might be transferred to sdk user, this option controls how
large each file can be. A smaller size may mean more calls will be needed
to transfer large consoles, which may not be desirable for performance reasons.
    '''),
    # monitor options
    Opt('cache_interval',
        section='monitor',
        default=600,
        opt_type='int',
        help='''
Cached monitor data update interval

This is used to prevent excessive effort spent retrieving the
monitor data by calling the SDK backend utilities. When this cache
is enabled, a inspect call will only call the SDK backend utilities
when the inspected guest's info does not exist in the cache or
when the cache data is expired. And when an cache update is needed,
all the existing guests' data will be retrieved in a single call to
the backend.

When this value is below or equal to zero, the cache
will be disabled and each inspect call will need to call the backend
utilities to get the inspected guest's monitor data.
        '''
        ),
    # wsgi options
    # this option is used when sending http request
    # to sdk wsgi, default to none so no token validation
    # will be used.
    Opt('auth',
        section='wsgi',
        default='none',
        opt_type='str',
        help='''
Whether auth will be used.

When sending http request from outside to running zvmsdk,
Client will be requested to input username/password in order
to authorize the call.
Set this to 'none' indicated no auth will be used and 'auth'
means username and password need to be specified.

Possible value:
'none': no auth will be required
'auth': need auth, currently pyjwt is used to return a token
        to caller if the username and password is correct.
''',
        ),
    Opt('token_validation_period',
        section='wsgi',
        default=30,
        opt_type='int',
        help='''
How long the token is valid.

If a token auth is used, the token return to user will be
expired after the period passed. This ensure an user who
get this token will not be authorized all the time, a new
token need to be recreated after certain time period.
''',
        ),
    Opt('user',
        section='wsgi',
        opt_type='str',
        help='''
Admin user to access sdk http server.

User in order to get a token from zvm sdk, and the token
will be used to validate request before token expire.
'''
        ),
    Opt('password',
        section='wsgi',
        opt_type='str',
        help='''
Admin password to access sdk http server.

Password in order to get a token from zvm sdk, and the token
will be used to validate request before token expire.
'''
        ),
    # Daemon server options
    Opt('bind_addr',
        section='sdkserver',
        default='127.0.0.1',
        opt_type='str',
        help='''
The IP address that the SDK server is listen on.

When the SDK server deamon starts, it will try to bind to
this address and port bind_port, and wait for the SDK client
connection to handle API request.
'''
        ),
    Opt('bind_port',
        section='sdkserver',
        opt_type='int',
        default=2000,
        help='''
The port that the SDK server is listen on.

This will work as a pair with bind_addr when the SDK server daemon
starts, more info can be found in that configuration description.
'''
        ),
    Opt('connect_type',
        section='sdkserver',
        opt_type='str',
        default='rest',
        help='''
The connection type of the requests flowing into the sdkserver.

This will work as a pair with bind_addr when the SDK server daemon
starts, more info can be found in that configuration description.
'''
        ),
    Opt('request_queue_size',
        section='sdkserver',
        opt_type='int',
        default=128,
        help='''
The size of request queue in SDK server.

SDK server maintains a queue to keep all the accepted but not handled requests,
and the SDK server workers fetch requests from this queue.
To some extend, this queue size decides the max socket opened in SDK server.
This value should be adjusted according to the system resource.
'''
        ),
    Opt('max_worker_count',
        section='sdkserver',
        opt_type='int',
        default=64,
        help='''
The maximum number of worker thread in SDK server to handle client requests.

These worker threads would work concurrently to handle requests from client.
This value should be adjusted according to the system resource and workload.
'''
        ),
    # database options
    Opt('dir',
        section='database',
        default='/var/lib/zvmsdk/databases/',
        opt_type='str',
        help='''
Directory to store database.

SDK databases are used to store a set of tables which contain the
information of network, volume, image, etc. This option is used to
tell SDK where to store the database files, make sure the process
running SDK is able to read write and execute the directory.
'''
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
    ]


class ConfigOpts(object):

    def __init__(self):
        self.dicts = {}

    def get_config_dicts_default(self, opts):
        _dict = {}
        for opt in opts:
            sec = opt.section
            if _dict.get(sec) is None:
                _dict[sec] = {}
            _dict[sec][opt.name] = {'required': opt.required,
                                    'default': opt.default,
                                    'type': opt.opt_type,
                                    'help': opt.help}
        return _dict

    def register(self, opts):
        configs = self.get_config_dicts_default(opts)
        read_file = self.find_config_file(project="zvmsdk") or ''
        if read_file:
            cf = ConfigParser.ConfigParser()
            cf.read(read_file)
            # return all sections in a list
            secs = cf.sections()
            config_dicts_override = self.config_ini_to_dicts(secs, cf)

            try:
                configs = self.merge(configs, config_dicts_override)
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

        con = self.toDict(con)
        return con

    def _check_required(self, conf):
        '''Check that all opts marked as required have values specified.'''
        for k1, v1 in conf.items():
            for k2, v2 in v1.items():
                if v2.required and (v2.default is None):
                    raise RequiredOptMissingError(k1, k2)

    def _check_type(self, conf):
        for v1 in conf.values():
            for k2, v2 in v1.items():
                if v2.type == 'int':
                    v2.default = int(v2.default)

    def _config_fill_option(self, conf):
        for k, v in conf.items():
            confs = {}
            for dk, dv in v.items():
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
        path = ''
        for d in dirs:
            path = os.path.join(d, '%s%s' % (basename, extension))
            if os.path.exists(path):
                return path

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
CONF = CONF.register(zvm_opts)
