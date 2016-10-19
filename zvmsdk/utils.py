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

import contextlib
import functools
import json
import os
import pwd

from six.moves import http_client as httplib
import socket
import time

import config as CONF
import constants as const
from log import LOG


_XCAT_URL = None


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


def get_xcat_url():
    global _XCAT_URL

    if _XCAT_URL is not None:
        return _XCAT_URL

    _XCAT_URL = XCATUrl()
    return _XCAT_URL


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
