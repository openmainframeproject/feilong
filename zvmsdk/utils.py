# Copyright 2013 IBM Corp.
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


import pdb
import contextlib
import functools
import json
import os
import pwd
import shutil

import six
from six.moves import http_client as httplib
import socket
import time

import tarfile
import tempfile
import stat
import errno

import config as CONF

import constants as const
from log import LOG


_XCAT_URL = None
_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


class ZVMException(Exception):
    def __init__(self, msg=None):
        super(ZVMException, self).__init__(msg)


class XCATUrl(object):
    """To return xCAT URLs for invoking xCAT REST APIs."""

    def __init__(self):
        self.PREFIX = '/xcatws'
        self.SUFFIX = ''.join(('?userName=', CONF.zvm_xcat_username,
                               '&password=', CONF.zvm_xcat_password,
                               '&format=json'))

        # xcat objects
        self.NODES = '/nodes'
        self.TABLES = '/tables'

        # xcat actions
        self.POWER = '/power'
        self.XDSH = '/dsh'
        
        self.VMS = '/vms'
        self.IMAGES = '/images'
        self.OBJECTS = '/objects/osimage'
        self.OS = '/OS'
        self.HV = '/hypervisor'
        self.NETWORK = '/networks'

        self.INVENTORY = '/inventory'
        self.STATUS = '/status'
        self.MIGRATE = '/migrate'
        self.CAPTURE = '/capture'
        self.EXPORT = '/export'
        self.IMGIMPORT = '/import'
        self.BOOTSTAT = '/bootstate'
        self.VERSION = '/version'
        self.PCONTEXT = '&requestid='
        self.PUUID = '&objectid='
        self.DIAGLOGS = '/logs/diagnostics'
        self.PNODERANGE = '&nodeRange='
        
    def _nodes(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.SUFFIX
    
    def _vms(self, arg='', vmuuid='', context=None):
        rurl = self.PREFIX + self.VMS + arg + self.SUFFIX
        return rurl

    def _append_addp(self, rurl, addp=None):
        if addp is not None:
            return ''.join((rurl, addp))
        else:
            return rurl

    def rpower(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.POWER + self.SUFFIX

    def xdsh(self, arg=''):
        """Run shell command."""
        return ''.join((self.PREFIX, self.NODES, arg, self.XDSH, self.SUFFIX))

    def gettab(self, arg='', addp=None):
        rurl = ''.join((self.PREFIX, self.TABLES, arg, self.SUFFIX))
        return self._append_addp(rurl, addp)

    def tabdump(self, arg='', addp=None):
        rurl = self.PREFIX + self.TABLES + arg + self.SUFFIX
        return self._append_addp(rurl, addp)

    def lsdef_node(self, arg='', addp=None):
        rurl = self.PREFIX + self.NODES + arg + self.SUFFIX
        return self._append_addp(rurl, addp)

    def mkdef(self, arg=''):
        return self._nodes(arg)

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
    
    def nodestat(self, arg=''):
        return self.PREFIX + self.NODES + arg + self.STATUS + self.SUFFIX
    
    def rmvm(self, arg='', vmuuid='', context=None):
        rurl = self._vms(arg, vmuuid, context)
        return rurl
    
class XCATConnection(object):
    """Https requests to xCAT web service."""

    def __init__(self):
        """Initialize https connection to xCAT service."""
        self.host = CONF.zvm_xcat_server
        self.conn = httplib.HTTPSConnection(self.host)

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

        _rep_ptn = ''.join(('&password=', CONF.zvm_xcat_password))
        LOG.debug("Sending request to xCAT. xCAT-Server:%(xcat_server)s "
                  "Request-method:%(method)s "
                  "URL:%(url)s "
                  "Headers:%(headers)s "
                  "Body:%(body)s" %
                  {'xcat_server': CONF.zvm_xcat_server,
                   'method': method,
                   'url': url.replace(_rep_ptn, ''),  # hide password in log
                   'headers': str(headers),
                   'body': body})

        try:
            self.conn.request(method, url, body, headers)
        except socket.gaierror as err:
            msg = ("Failed to connect xCAT server %(srv)s: %(err)s" %
                   {'srv': self.host, 'err': err})
            raise ZVMException(msg)
        except (socket.error, socket.timeout) as err:
            msg = ("Communicate with xCAT server %(srv)s error: %(err)s" %
                   {'srv': self.host, 'err': err})
            raise ZVMException(msg)

        try:
            res = self.conn.getresponse()
        except Exception as err:
            msg = ("Failed to get response from xCAT server %(srv)s: "
                     "%(err)s" % {'srv': self.host, 'err': err})
            raise ZVMException(msg)

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
            raise ZVMException(msg)

        return resp

def get_xcat_url():
    global _XCAT_URL

    if _XCAT_URL is not None:
        return _XCAT_URL

    _XCAT_URL = XCATUrl()
    return _XCAT_URL


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
        raise ZVMException(msg=errmsg)


@contextlib.contextmanager
def expect_invalid_xcat_resp_data(data=''):
    """Catch exceptions when using xCAT response data."""
    try:
        yield
    except (ValueError, TypeError, IndexError, AttributeError,
            KeyError) as err:
        LOG.error('Parse %s encounter error', data)
        raise ZVMException(msg=err)


def wrap_invalid_xcat_resp_data_error(function):
    """Catch exceptions when using xCAT response data."""

    @functools.wraps(function)
    def decorated_function(*arg, **kwargs):
        try:
            return function(*arg, **kwargs)
        except (ValueError, TypeError, IndexError, AttributeError,
                KeyError) as err:
            raise ZVMException(msg=err)

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
        raise ZVMException(msg=msg)

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
                raise ZVMException(msg=message)

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


def get_host():
    return ''.join([pwd.getpwuid(os.geteuid()).pw_name, '@', CONF.my_ip])


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


def punch_adminpass_file(instance_path, instance_name, admin_password,
                         linuxdist):
    adminpass_fn = ''.join([instance_path, '/adminpwd.sh'])
    _generate_adminpass_file(adminpass_fn, admin_password, linuxdist)
    punch_file(instance_name, adminpass_fn, 'X')


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
        LOG.debug("*********-============timeout is %(timeout)s, expiration is %(expiration)s, time_start is %(time_start)s" % 
                  {"timeout": timeout, "expiration": expiration, "time_start": time_start})

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


def create_xcat_node(instance_name, zhcp, userid=None):
    """Create xCAT node for z/VM instance."""
    LOG.debug("Creating xCAT node for %s" % instance_name)

    user_id = instance_name
    body = ['userid=%s' % user_id,
            'hcp=%s' % zhcp,
            'mgt=zvm',
            'groups=%s' % const.ZVM_XCAT_GROUP]
    url = get_xcat_url().mkdef('/' + instance_name)

    xcat_request("POST", url, body)

    
def _get_instances_path():
        return os.path.normpath(CONF.instances_path)
    
def get_instance_path(os_node, instance_name):
    instance_folder = os.path.join(_get_instances_path(), os_node,
                                   instance_name)
    if not os.path.exists(instance_folder):
        LOG.debug("Creating the instance path %s", instance_folder)
        os.makedirs(instance_folder)
    return instance_folder
            
def add_xcat_host(node, ip, host_name):
    """Add/Update hostname/ip bundle in xCAT MN nodes table."""
    commands = "node=%s" % node + " hosts.ip=%s" % ip
    commands += " hosts.hostnames=%s" % host_name
    body = [commands]
    url = get_xcat_url().tabch("/hosts")

    
    result_data = xcat_request("PUT", url, body)['data']

    return result_data

def config_xcat_mac(instance_name):
    """Hook xCat to prevent assign MAC for instance."""
    fake_mac_addr = "00:00:00:00:00:00"
    nic_name = "fake"
    add_xcat_mac(instance_name, nic_name, fake_mac_addr)
    
def add_xcat_mac(node, interface, mac, zhcp=None):
    """Add node name, interface, mac address into xcat mac table."""
    commands = "mac.node=%s" % node + " mac.mac=%s" % mac
    commands += " mac.interface=%s" % interface
    if zhcp is not None:
        commands += " mac.comments=%s" % zhcp
    url = get_xcat_url().tabch("/mac")
    body = [commands]
    return xcat_request("PUT", url, body)['data']
    
def makehosts():
    """Update xCAT MN /etc/hosts file."""
    url = get_xcat_url().network("/makehosts")
    return xcat_request("PUT", url)['data']

def create_xcat_table_about_nic(zhcpnode, inst_name,
                                nic_name, mac_address, vdev):
    _delete_xcat_mac(inst_name)
    add_xcat_mac(inst_name, vdev, mac_address, zhcpnode)
    add_xcat_switch(inst_name, nic_name, vdev, zhcpnode)
    
def _delete_xcat_mac(node_name):
    """Remove node mac record from xcat mac table."""
    commands = "-d node=%s mac" % node_name
    url = get_xcat_url().tabch("/mac")
    body = [commands]

    return xcat_request("PUT", url, body)['data']

def add_xcat_switch(node, nic_name, interface, zhcp=None):
    """Add node name and nic name address into xcat switch table."""
    commands = "switch.node=%s" % node
    commands += " switch.port=%s" % nic_name
    commands += " switch.interface=%s" % interface
    if zhcp is not None:
        commands += " switch.comments=%s" % zhcp
    url = get_xcat_url().tabch("/switch")
    body = [commands]

    return xcat_request("PUT", url, body)['data']

def update_node_info(instance_name, image_name, os_version, image_id):
    LOG.debug("Update the node info for instance %s", instance_name)

    profile_name = '_'.join((image_name, image_id.replace('-', '_')))

    body = ['noderes.netboot=%s' % const.HYPERVISOR_TYPE,
            'nodetype.os=%s' % os_version,
            'nodetype.arch=%s' % const.ARCHITECTURE,
            'nodetype.provmethod=%s' % const.PROV_METHOD,
            'nodetype.profile=%s' % profile_name]
    url = get_xcat_url().chtab('/' + instance_name)

    xcat_request("PUT", url, body)
    
def deploy_node(instance_name, image_name, transportfiles=None, vdev=None):
    LOG.debug("Begin to deploy image on instance %s", instance_name)
    vdev = vdev or CONF.zvm_user_root_vdev
    remote_host_info = get_host()
    body = ['netboot',
            'device=%s' % vdev,
            'osimage=%s' % image_name]

    if transportfiles:
        body.append('transport=%s' % transportfiles)
        body.append('remotehost=%s' % remote_host_info)

    url = get_xcat_url().nodeset('/' + instance_name)

    xcat_request("PUT", url, body)
    
def punch_xcat_auth_file(instance_path, instance_name):
    """Make xCAT MN authorized by virtual machines."""
    mn_pub_key = get_mn_pub_key()
    auth_fn = ''.join([instance_path, '/xcatauth.sh'])
    _generate_auth_file(auth_fn, mn_pub_key)
    punch_file(instance_name, auth_fn, 'X')
    
def get_mn_pub_key():
    cmd = 'cat /root/.ssh/id_rsa.pub'
    resp = xdsh(CONF.zvm_xcat_master, cmd)
    key = resp['data'][0][0]
    start_idx = key.find('ssh-rsa')
    key = key[start_idx:]
    return key

def _generate_auth_file(fn, pub_key):
    lines = ['#!/bin/bash\n',
    'echo "%s" >> /root/.ssh/authorized_keys' % pub_key]
    with open(fn, 'w') as f:
        f.writelines(lines)
    
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
        raise ZVMException(msg=errmsg)
    
def get_imgname_xcat(image_id):
    """Get the xCAT deployable image name by image id."""
    image_uuid = image_id.replace('-', '_')
    parm = '&criteria=profile=~' + image_uuid
    url = get_xcat_url().lsdef_image(addp=parm)

    res = xcat_request("GET", url)
    res_image = res['info'][0][0]
    res_img_name = res_image.strip().split(" ")[0]

    if res_img_name:
        return res_img_name
    else:
        LOG.error("Fail to find the right image to deploy")
            
def clean_mac_switch_host(node_name):
    """Clean node records in xCAT mac, host and switch table."""
    clean_mac_switch(node_name)
    _delete_xcat_host(node_name)
    
def clean_mac_switch(node_name):
    """Clean node records in xCAT mac and switch table."""
    _delete_xcat_mac(node_name)
    _delete_xcat_switch(node_name)
    
def _delete_xcat_switch(node_name):
    """Remove node switch record from xcat switch table."""
    commands = "-d node=%s switch" % node_name
    url = get_xcat_url().tabch("/switch")
    body = [commands]

    return xcat_request("PUT", url, body)['data']

def _delete_xcat_host(node_name):
    """Remove xcat hosts table rows where node name is node_name."""
    commands = "-d node=%s hosts" % node_name
    body = [commands]
    url = get_xcat_url().tabch("/hosts")

    return xcat_request("PUT", url, body)['data']

def parse_image_name(os_image_name):
    profile = os_image_name.split('-')[3]
    image_name = profile.split('_')[0]
    xcat_image_id = profile.split('_', 1)[1]
    image_id = xcat_image_id.replace('_', '-')
    return image_name, image_id

def get_image_version(os_image_name):
    os_version = os_image_name.split('-')[0]
    return os_version