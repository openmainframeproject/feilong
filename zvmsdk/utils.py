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


import contextlib
import commands
import errno
import functools
import json
import os
import pwd
import re
import ssl
import shutil
import six
import socket
import stat
import time
import types

from six.moves import http_client as httplib

from zvmsdk import config
from zvmsdk import exception
from zvmsdk import log

import constants as const


CONF = config.CONF
LOG = log.LOG
_XCAT_URL = None
_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


class XCATUrl(object):
    """To return xCAT URLs for invoking xCAT REST APIs."""

    def __init__(self):
        self.PREFIX = '/xcatws'
        self.SUFFIX = ''.join(('?userName=', CONF.xcat.username,
                               '&password=', CONF.xcat.password,
                               '&format=json'))

        # xcat objects
        self.VMS = '/vms'
        self.NODES = '/nodes'
        self.TABLES = '/tables'
        self.IMAGES = '/images'
        self.OBJECTS = '/objects/osimage'
        self.OS = '/OS'
        self.HV = '/hypervisor'
        self.NETWORK = '/networks'

        # xcat actions
        self.POWER = '/power'
        self.STATUS = '/status'
        self.XDSH = '/dsh'
        self.CAPTURE = '/capture'
        self.IMGIMPORT = '/import'
        self.INVENTORY = '/inventory'
        self.STATUS = '/status'
        self.MIGRATE = '/migrate'
        self.CAPTURE = '/capture'
        self.EXPORT = '/export'
        self.IMGIMPORT = '/import'
        self.BOOTSTAT = '/bootstate'
        self.VERSION = '/version'
        self.DIAGLOGS = '/logs/diagnostics'
        self.PNODERANGE = '&nodeRange='

    def _nodes(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.SUFFIX

    def _vms(self, arg=''):
        rurl = self.PREFIX + self.VMS + arg + self.SUFFIX
        return rurl

    def _append_addp(self, rurl, addp=None):
        if addp is not None:
            return ''.join((rurl, addp))
        else:
            return rurl

    def _hv(self, arg=''):
        return self.PREFIX + self.HV + arg + self.SUFFIX

    def rpower(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.POWER + self.SUFFIX

    def nodestat(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.STATUS + self.SUFFIX

    def mkdef(self, arg=''):
        return self._nodes(arg)

    def rmdef(self, arg=''):
        return self._nodes(arg)

    def xdsh(self, arg=''):
        """Run shell command."""
        return ''.join((self.PREFIX, self.NODES, arg, self.XDSH, self.SUFFIX))

    def capture(self, arg=''):
        return self.PREFIX + self.IMAGES + arg + self.CAPTURE + self.SUFFIX

    def rmimage(self, arg=''):
        return self.PREFIX + self.IMAGES + arg + self.SUFFIX

    def rmobject(self, arg=''):
        return self.PREFIX + self.OBJECTS + arg + self.SUFFIX

    def imgimport(self, arg=''):
        return self.PREFIX + self.IMAGES + self.IMGIMPORT + arg + self.SUFFIX

    def gettab(self, arg='', addp=None):
        rurl = ''.join((self.PREFIX, self.TABLES, arg, self.SUFFIX))
        return self._append_addp(rurl, addp)

    def tabdump(self, arg='', addp=None):
        rurl = self.PREFIX + self.TABLES + arg + self.SUFFIX
        return self._append_addp(rurl, addp)

    def lsdef_node(self, arg='', addp=None):
        rurl = self.PREFIX + self.NODES + arg + self.SUFFIX
        return self._append_addp(rurl, addp)

    def mkvm(self, arg=''):
        rurl = self._vms(arg)
        return rurl

    def chvm(self, arg=''):
        return self._vms(arg)

    def network(self, arg='', addp=None):
        rurl = self.PREFIX + self.NETWORK + arg + self.SUFFIX
        if addp is not None:
            return rurl + addp
        else:
            return rurl

    def chtab(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.SUFFIX

    def nodeset(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.BOOTSTAT + self.SUFFIX

    def rinv(self, arg='', addp=None):
        rurl = self.PREFIX + self.NODES + arg + self.INVENTORY + self.SUFFIX
        return self._append_addp(rurl, addp)

    def tabch(self, arg='', addp=None):
        """Add/update/delete row(s) in table arg, with attribute addp."""
        rurl = self.PREFIX + self.TABLES + arg + self.SUFFIX
        return self._append_addp(rurl, addp)

    def lsdef_image(self, arg='', addp=None):
        rurl = self.PREFIX + self.IMAGES + arg + self.SUFFIX
        return self._append_addp(rurl, addp)

    def rmvm(self, arg=''):
        rurl = self._vms(arg)
        return rurl

    def lsvm(self, arg=''):
        rurl = self._vms(arg)
        return rurl

    def version(self):
        return self.PREFIX + self.VERSION + self.SUFFIX

    def chhv(self, arg=''):
        return self._hv(arg)


class XCATConnection(object):
    """Https requests to xCAT web service."""

    def __init__(self):
        """Initialize https connection to xCAT service."""
        self.port = 443
        self.host = CONF.xcat.server
        self.conn = HTTPSClientAuthConnection(self.host, self.port,
                        CONF.xcat.ca_file,
                        timeout=CONF.xcat.connection_timeout)

    def request(self, method, url, body=None, headers={}):
        """Send https request to xCAT server.

        Will return a python dictionary including:
        {'status': http return code,
         'reason': http reason,
         'message': response message}

        """
        if body is not None:
            body = json.dumps(body)
            headers = {'content-type': 'text/plain',
                       'content-length': len(body)}

        _rep_ptn = ''.join(('&password=', CONF.xcat.password))
        LOG.debug("Sending request to xCAT. xCAT-Server:%(xcat_server)s "
                  "Request-method:%(method)s "
                  "URL:%(url)s "
                  "Headers:%(headers)s "
                  "Body:%(body)s" %
                  {'xcat_server': CONF.xcat.server,
                   'method': method,
                   'url': url.replace(_rep_ptn, ''),  # hide password in log
                   'headers': str(headers),
                   'body': body})

        try:
            self.conn.request(method, url, body, headers)
        except socket.gaierror as err:
            msg = ("Failed to connect xCAT server %(srv)s: %(err)s" %
                   {'srv': self.host, 'err': err})
            raise exception.ZVMXCATRequestFailed(msg)
        except (socket.error, socket.timeout) as err:
            msg = ("Communicate with xCAT server %(srv)s error: %(err)s" %
                   {'srv': self.host, 'err': err})
            raise exception.ZVMXCATRequestFailed(msg)

        try:
            res = self.conn.getresponse()
        except Exception as err:
            msg = ("Failed to get response from xCAT server %(srv)s: "
                     "%(err)s" % {'srv': self.host, 'err': err})
            raise exception.ZVMXCATRequestFailed(msg)

        msg = res.read()
        resp = {
            'status': res.status,
            'reason': res.reason,
            'message': msg}

        LOG.debug("xCAT response: %s" % str(resp))

        # Only "200" or "201" returned from xCAT can be considered
        # as good status
        err = None
        if method == "POST":
            if res.status != 201:
                err = str(resp)
        else:
            if res.status != 200:
                err = str(resp)

        if err is not None:
            msg = ('Request to xCAT server %(srv)s failed:  %(err)s' %
                   {'srv': self.host, 'err': err})
            raise exception.ZVMXCATRequestFailed(msg)

        return resp


class HTTPSClientAuthConnection(httplib.HTTPSConnection):
    """For https://wiki.openstack.org/wiki/OSSN/OSSN-0033"""

    def __init__(self, host, port, ca_file, timeout=None, key_file=None,
                 cert_file=None):
        httplib.HTTPSConnection.__init__(self, host, port,
                                         key_file=key_file,
                                         cert_file=cert_file)
        self.key_file = key_file
        self.cert_file = cert_file
        self.ca_file = ca_file
        self.timeout = timeout
        self.use_ca = True

        if self.ca_file is None:
            LOG.debug("no xCAT CA file specified, this is considered "
                      "not secure")
            self.use_ca = False

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        if (self.ca_file is not None and
            not os.path.exists(self.ca_file)):
            LOG.warning(("the CA file %(ca_file) does not exist!"),
                        {'ca_file': self.ca_file})
            self.use_ca = False

        if not self.use_ca:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        cert_reqs=ssl.CERT_NONE)
        else:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file,
                                        ca_certs=self.ca_file,
                                        cert_reqs=ssl.CERT_REQUIRED)


def get_xcat_url():
    global _XCAT_URL

    if _XCAT_URL is not None:
        return _XCAT_URL

    _XCAT_URL = XCATUrl()
    return _XCAT_URL


def remove_prefix_of_unicode(str_unicode):
    str_unicode = str_unicode.encode('unicode_escape')
    str_unicode = str_unicode.replace('\u', '')
    str_unicode = str_unicode.decode('utf-8')
    return str_unicode


def xcat_request(method, url, body=None, headers=None):
    headers = headers or {}
    conn = XCATConnection()
    resp = conn.request(method, url, body, headers)
    return load_xcat_resp(resp['message'])


def jsonloads(jsonstr):
    try:
        return json.loads(jsonstr)
    except ValueError:
        errmsg = "xCAT response data is not in JSON format"
        LOG.error(errmsg)
        raise exception.ZVMInvalidXCATResponseDataError(msg=errmsg)


@contextlib.contextmanager
def expect_invalid_xcat_resp_data(data=''):
    """Catch exceptions when using xCAT response data."""
    try:
        yield
    except (ValueError, TypeError, IndexError, AttributeError,
            KeyError) as err:
        LOG.error('Parse %s encounter error', data)
        raise exception.ZVMInvalidXCATResponseDataError(msg=err)


@contextlib.contextmanager
def expect_xcat_call_failed_and_reraise(exc, **kwargs):
    """Catch all kinds of xCAT call failure and reraise.

    exc: the exception that would be raised.
    """
    try:
        yield
    except (exception.ZVMXCATRequestFailed,
            exception.ZVMInvalidXCATResponseDataError,
            exception.ZVMXCATInternalError) as err:
        msg = err.format_message()
        kwargs['msg'] = msg
        LOG.error('XCAT response return error: %s', msg)
        raise exc(**kwargs)


@contextlib.contextmanager
def expect_invalid_xcat_node_and_reraise(userid):
    """Catch <Invalid nodes and/or groups in noderange: > and reraise."""
    try:
        yield
    except (exception.ZVMXCATRequestFailed,
            exception.ZVMXCATInternalError) as err:
        msg = err.format_message()
        if "Invalid nodes and/or groups" in msg:
            raise exception.ZVMVirtualMachineNotExist(
                    zvm_host=CONF.zvm.host, userid=userid)
        else:
            raise err


def wrap_invalid_xcat_resp_data_error(function):
    """Catch exceptions when using xCAT response data."""

    @functools.wraps(function)
    def decorated_function(*arg, **kwargs):
        try:
            return function(*arg, **kwargs)
        except (ValueError, TypeError, IndexError, AttributeError,
                KeyError) as err:
            raise exception.ZVMInvalidXCATResponseDataError(msg=err)

    return decorated_function


@wrap_invalid_xcat_resp_data_error
def translate_xcat_resp(rawdata, dirt):
    """Translate xCAT response JSON stream to a python dictionary.

    xCAT response example:
    node: keyword1: value1\n
    node: keyword2: value2\n
    ...
    node: keywordn: valuen\n

    Will return a python dictionary:
    {keyword1: value1,
     keyword2: value2,
     ...
     keywordn: valuen,}

    """
    data_list = rawdata.split("\n")

    data = {}

    for ls in data_list:
        for k in list(dirt.keys()):
            if ls.__contains__(dirt[k]):
                data[k] = ls[(ls.find(dirt[k]) + len(dirt[k])):].strip()
                break

    if data == {}:
        msg = "No value matched with keywords. Raw Data: %(raw)s; " \
                "Keywords: %(kws)s" % {'raw': rawdata, 'kws': str(dirt)}
        raise exception.ZVMInvalidXCATResponseDataError(msg=msg)

    return data


@wrap_invalid_xcat_resp_data_error
def load_xcat_resp(message):
    """Abstract information from xCAT REST response body.

    As default, xCAT response will in format of JSON and can be
    converted to Python dictionary, would looks like:
    {"data": [{"info": [info,]}, {"data": [data,]}, ..., {"error": [error,]}]}

    Returns a Python dictionary, looks like:
    {'info': [info,],
     'data': [data,],
     ...
     'error': [error,]}

    """
    resp_list = jsonloads(message)['data']
    keys = const.XCAT_RESPONSE_KEYS

    resp = {}

    for k in keys:
        resp[k] = []

    for d in resp_list:
        for k in keys:
            if d.get(k) is not None:
                resp[k].append(d.get(k))

    err = resp.get('error')
    if err != []:
        for e in err:
            if _is_warning_or_recoverable_issue(str(e)):
                # ignore known warnings or errors:
                continue
            else:
                raise exception.ZVMXCATInternalError(msg=message)

    _log_warnings(resp)

    return resp


def _log_warnings(resp):
    for msg in (resp['info'], resp['node'], resp['data']):
        msgstr = str(msg)
        if 'warn' in msgstr.lower():
            LOG.info("Warning from xCAT: %s" % msgstr)


def _is_warning_or_recoverable_issue(err_str):
    return _is_warning(err_str) or _is_recoverable_issue(err_str)


def _is_recoverable_issue(err_str):
    dirmaint_request_counter_save = ['Return Code: 596', 'Reason Code: 1185']
    recoverable_issues = [dirmaint_request_counter_save]
    for issue in recoverable_issues:
        # Search all matchs in the return value
        # any mismatch leads to recoverable not empty
        recoverable = [t for t in issue if t not in err_str]
        if recoverable == []:
            return True

    return False


def _is_warning(err_str):
    ignore_list = (
        'Warning: the RSA host key for',
        'Warning: Permanently added',
        'WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED',
    )

    for im in ignore_list:
        if im in err_str:
            return True

    return False


def get_userid(node_name):
    """Returns z/VM userid for the xCAT node."""
    url = get_xcat_url().lsdef_node(''.join(['/', node_name]))
    info = xcat_request('GET', url)
    with expect_invalid_xcat_resp_data(info):
        for s in info['info'][0]:
            if s.__contains__('userid='):
                return s.strip().rpartition('=')[2]


def xdsh(node, commands):
    """"Run command on xCAT node."""
    LOG.debug('Run command %(cmd)s on xCAT node %(node)s' %
              {'cmd': commands, 'node': node})

    def xdsh_execute(node, commands):
        """Invoke xCAT REST API to execute command on node."""
        xdsh_commands = 'command=%s' % commands
        # Add -q (quiet) option to ignore ssh warnings and banner msg
        opt = 'options=-q'
        body = [xdsh_commands, opt]
        url = get_xcat_url().xdsh('/' + node)
        return xcat_request("PUT", url, body)

    res_dict = xdsh_execute(node, commands)

    return res_dict


def execute(cmd):
    """execute command in shell and return output"""
    # TODO:do some exception in future
    status, output = commands.getstatusoutput(cmd)
    # if success status will be 0
    # if status != 0:
    return output


def get_host():
    return ''.join([pwd.getpwuid(os.geteuid()).pw_name, '@',
                    CONF.network.my_ip])


def punch_file(node, fn, fclass):
    body = [" ".join(['--punchfile', fn, fclass, get_host()])]
    url = get_xcat_url().chvm('/' + node)

    try:
        xcat_request("PUT", url, body)
    except Exception as err:
        LOG.error('Punch file to %(node)s failed: %(msg)s' %
                      {'node': node, 'msg': err})
    finally:
        os.remove(fn)


def punch_adminpass_file(temp_path, userid, admin_password,
                         linuxdist):
    adminpass_fn = ''.join([temp_path, '/adminpwd.sh'])
    _generate_adminpass_file(adminpass_fn, admin_password, linuxdist)
    punch_file(userid, adminpass_fn, 'X')


def _generate_adminpass_file(fn, admin_password, linuxdist):
    pwd_str = linuxdist.get_change_passwd_command(admin_password)
    lines = ['#!/bin/bash\n', pwd_str]
    with open(fn, 'w') as f:
        f.writelines(lines)


def looping_call(f, sleep=5, inc_sleep=0, max_sleep=60, timeout=600,
                 exceptions=(), *args, **kwargs):
    """Helper function that to run looping call with fixed/dynamical interval.

    :param f:          the looping call function or method.
    :param sleep:      initial interval of the looping calls.
    :param inc_sleep:  sleep time increment, default as 0.
    :param max_sleep:  max sleep time.
    :param timeout:    looping call timeout in seconds, 0 means no timeout.
    :param exceptions: exceptions that trigger re-try.

    """
    time_start = time.time()
    expiration = time_start + timeout

    retry = True
    while retry:
        expired = timeout and (time.time() > expiration)
        LOG.debug(
                "timeout is %(timeout)s, expiration is %(expiration)s, \
                        time_start is %(time_start)s" %
                        {"timeout": timeout, "expiration": expiration,
                            "time_start": time_start})

        try:
            f(*args, **kwargs)
        except exceptions:
            retry = not expired
            if retry:
                LOG.debug("Will re-try %(fname)s in %(itv)d seconds" %
                          {'fname': f.__name__, 'itv': sleep})
                time.sleep(sleep)
                sleep = min(sleep + inc_sleep, max_sleep)
            else:
                LOG.debug("Looping call %s timeout" % f.__name__)
            continue
        retry = False


def punch_xcat_auth_file(temp_path, userid):
    """Make xCAT MN authorized by virtual machines."""
    mn_pub_key = get_mn_pub_key()
    auth_fn = ''.join([temp_path, '/xcatauth.sh'])
    _generate_auth_file(auth_fn, mn_pub_key)
    punch_file(userid, auth_fn, 'X')


def get_mn_pub_key():
    cmd = 'cat /root/.ssh/id_rsa.pub'
    resp = xdsh(CONF.xcat.master_node, cmd)
    key = resp['data'][0][0]
    start_idx = key.find('ssh-rsa')
    key = key[start_idx:]
    return key


def _generate_auth_file(fn, pub_key):
    lines = ['#!/bin/bash\n',
    'echo "%s" >> /root/.ssh/authorized_keys' % pub_key]
    with open(fn, 'w') as f:
        f.writelines(lines)


def parse_image_name(os_image_name):
    profile = os_image_name.split('-')[3]
    image_name = profile.split('_')[0]
    xcat_image_id = profile.split('_', 1)[1]
    image_id = xcat_image_id.replace('_', '-')
    return image_name, image_id


def get_image_version(os_image_name):
    os_version = os_image_name.split('-')[0]
    return os_version


def get_xcat_version():
    """Return the version of xCAT."""

    url = get_xcat_url().version()
    with expect_invalid_xcat_resp_data():
        data = xcat_request('GET', url)['data']
        version = data[0][0].split()[1]
        version = version.strip()
        return version


def get_zhcp_node():
    """Return zhcp node."""
    return CONF.xcat.zhcp.partition('.')[0]


def convert_to_mb(s):
    """Convert memory size from GB to MB."""
    s = s.upper()
    try:
        if s.endswith('G'):
            return float(s[:-1].strip()) * 1024
        elif s.endswith('T'):
            return float(s[:-1].strip()) * 1024 * 1024
        else:
            return float(s[:-1].strip())
    except (IndexError, ValueError, KeyError, TypeError) as e:
        errmsg = ("Invalid memory format: %s") % e
        raise exception.ZVMSDKInteralError(msg=errmsg)


class PathUtils(object):
    def open(self, path, mode):
        """Wrapper on six.moves.builtins.open used to simplify unit testing."""
        return six.moves.builtins.open(path, mode)

    def _get_image_tmp_path(self):
        image_tmp_path = os.path.normpath(CONF.image.temp_path)
        if not os.path.exists(image_tmp_path):
            LOG.debug('Creating folder %s for image temp files',
                     image_tmp_path)
            os.makedirs(image_tmp_path)
        return image_tmp_path

    def get_bundle_tmp_path(self, tmp_file_fn):
        bundle_tmp_path = os.path.join(self._get_image_tmp_path(), "spawn_tmp",
                                       tmp_file_fn)
        if not os.path.exists(bundle_tmp_path):
            LOG.debug('Creating folder %s for image bundle temp file',
                      bundle_tmp_path)
            os.makedirs(bundle_tmp_path)
        return bundle_tmp_path

    def get_img_path(self, bundle_file_path, image_name):
        return os.path.join(bundle_file_path, image_name)

    def _get_snapshot_path(self):
        snapshot_folder = os.path.join(self._get_image_tmp_path(),
                                       "snapshot_tmp")
        if not os.path.exists(snapshot_folder):
            LOG.debug("Creating the snapshot folder %s", snapshot_folder)
            os.makedirs(snapshot_folder)
        return snapshot_folder

    def _get_punch_path(self):
        punch_folder = os.path.join(self._get_image_tmp_path(), "punch_tmp")
        if not os.path.exists(punch_folder):
            LOG.debug("Creating the punch folder %s", punch_folder)
            os.makedirs(punch_folder)
        return punch_folder

    def get_spawn_folder(self):
        spawn_folder = os.path.join(self._get_image_tmp_path(), "spawn_tmp")
        if not os.path.exists(spawn_folder):
            LOG.debug("Creating the spawn folder %s", spawn_folder)
            os.makedirs(spawn_folder)
        return spawn_folder

    def make_time_stamp(self):
        tmp_file_fn = time.strftime('%Y%m%d%H%M%S',
                                            time.localtime(time.time()))
        return tmp_file_fn

    def get_snapshot_time_path(self):
        snapshot_time_path = os.path.join(self._get_snapshot_path(),
                                          self.make_time_stamp())
        if not os.path.exists(snapshot_time_path):
            LOG.debug('Creating folder %s for image bundle temp file',
                      snapshot_time_path)
            os.makedirs(snapshot_time_path)
        return snapshot_time_path

    def clean_temp_folder(self, tmp_file_fn):
        if os.path.isdir(tmp_file_fn):
            LOG.debug('Removing existing folder %s ', tmp_file_fn)
            shutil.rmtree(tmp_file_fn)

    def _get_instances_path(self):
        return os.path.normpath(CONF.guest.temp_path)

    def get_instance_path(self, os_node, instance_name):
        instance_folder = os.path.join(self._get_instances_path(), os_node,
                                       instance_name)
        if not os.path.exists(instance_folder):
            LOG.debug("Creating the instance path %s", instance_folder)
            os.makedirs(instance_folder)
        return instance_folder

    def get_console_log_path(self, os_node, instance_name):
        return os.path.join(self.get_instance_path(os_node, instance_name),
                            "console.log")


def to_utf8(text):
    if isinstance(text, bytes):
        return text
    elif isinstance(text, six.text_type):
        return text.encode('utf-8')
    else:
        raise TypeError("bytes or Unicode expected, got %s"
                        % type(text).__name__)


def valid_userid(userid):
    if type(userid) not in types.StringTypes:
        return False
    if ((userid == '') or
        (userid.find(' ') != -1)):
        return False
    if len(userid) > 8:
        return False
    return True


def valid_mac_addr(addr):
    ''' Validates a mac address'''
    if type(addr) not in types.StringTypes:
        return False
    valid = re.compile(r'''
                      (^([0-9A-F]{1,2}[:]){5}([0-9A-F]{1,2})$)
                      ''',
                      re.VERBOSE | re.IGNORECASE)
    return valid.match(addr) is not None


def valid_IP(IPaddr):
    if type(IPaddr) not in types.StringTypes:
        return False
    q = IPaddr.split('.')
    return len(q) == 4 and len(filter(lambda x: x >= 0 and x <= 255,
                        map(int, filter(lambda x: x.isdigit(), q)))) == 4


def last_bytes(file_like_object, num):
    try:
        file_like_object.seek(-num, os.SEEK_END)
    except IOError as e:
        # seek() fails with EINVAL when trying to go before the start of the
        # file. It means that num is larger than the file size, so just
        # go to the start.
        if e.errno == errno.EINVAL:
            file_like_object.seek(0, os.SEEK_SET)
        else:
            raise

    remaining = file_like_object.tell()
    return (file_like_object.read(), remaining)


@wrap_invalid_xcat_resp_data_error
def create_xcat_mgt_network(mgt_vswitch):
    '''To talk to xCAT MN, xCAT MN requires every instance has a NIC which is
    in the same subnet as xCAT. The xCAT MN's IP address is mgt_ip,
    mask is mgt_mask in the config file,
    by default zvmsdk.conf.
    '''

    mgt_ip = CONF.xcat.mgt_ip
    mgt_mask = CONF.xcat.mgt_mask
    if (mgt_ip is None or
        mgt_mask is None):
        LOG.info("User does not configure management IP. Don't need to"
                 " initialize xCAT management network.")
        return

    xcat_node_name = CONF.xcat.master_node
    url = get_xcat_url().xdsh("/%s" % xcat_node_name)
    xdsh_commands = ('command=vmcp q v nic 800')
    body = [xdsh_commands]
    try:
        result = xcat_request("PUT", url, body)['data'][0][0]
    except exception.ZVMXCATInternalError as err:
        msg = err.format_message()
        output = re.findall('Error returned from xCAT: (.*)', msg)
        output_dict = json.loads(output[0])
        result = output_dict['data'][0]['data'][0]
    cmd = ''
    # nic does not exist
    if 'does not exist' in result:
        cmd = ('vmcp define nic 0800 type qdio\n' +
               'vmcp couple 0800 system %s\n' % (mgt_vswitch))
    # nic is created but not couple
    elif 'LAN: *' in result:
        cmd = ('vmcp couple 0800 system %s\n' % (mgt_vswitch))
    # couple and active
    elif "VSWITCH: SYSTEM" in result:
        # Only support one management network.
        url = get_xcat_url().xdsh("/%s") % xcat_node_name
        xdsh_commands = "command=ifconfig enccw0.0.0800|grep 'inet '"
        body = [xdsh_commands]
        result = xcat_request("PUT", url, body)
        if result['errorcode'][0][0] == '0' and result['data']:
            cur_ip = re.findall('inet (.*)  netmask',
                               result['data'][0][0])
            cur_mask = re.findall('netmask (.*)  broadcast',
                               result['data'][0][0])
            if not cur_ip:
                LOG.warning(("Nic 800 has been created, but IP "
                      "address is not correct, will config it again"))
            elif mgt_ip != cur_ip[0]:
                raise exception.zVMConfigException(
                    msg=("Only support one Management network,"
                         "it has been assigned by other agent!"
                         "Please use current management network"
                         "(%s/%s) to deploy." % (cur_ip[0], cur_mask)))
            else:
                LOG.debug("IP address has been assigned for NIC 800.")
                return
        else:
            LOG.warning(("Nic 800 has been created, but IP address "
                            "doesn't exist, will config it again"))
    else:
        message = ("Command 'query v nic' return %s,"
                   " it is unkown information for zvm-agent") % result
        LOG.error(("Error: %s") % message)
        raise exception.ZVMNetworkError(msg=message)
    url = get_xcat_url().xdsh("/%s") % xcat_node_name
    cmd += ('/usr/bin/perl /usr/sbin/sspqeth2.pl ' +
            '-a %s -d 0800 0801 0802 -e enccw0.0.0800 -m %s -g %s'
          % (mgt_ip, mgt_mask, mgt_ip))
    xdsh_commands = 'command=%s' % cmd
    body = [xdsh_commands]
    xcat_request("PUT", url, body)
