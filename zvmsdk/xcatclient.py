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
import datetime
import functools
import json
import os
import re
import shutil
import socket
import ssl
import stat
import tarfile
import xml.dom.minidom as Dom

from six.moves import http_client as httplib

from zvmsdk import client
from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG
_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO

_XCAT_URL = None


def get_xcat_url():
    global _XCAT_URL

    if _XCAT_URL is not None:
        return _XCAT_URL

    _XCAT_URL = XCATUrl()
    return _XCAT_URL


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
    dirmaint_request_limit = ['Return Code: 596', 'Reason Code: 6312']
    recoverable_issues = [
        dirmaint_request_counter_save,
        dirmaint_request_limit,
    ]
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


class XCATClient(client.ZVMClient):

    def __init__(self):
        self._xcat_url = get_xcat_url()
        self._zhcp_info = {}
        self._zhcp_userid = None
        self._xcat_node_name = None
        self._pathutils = zvmutils.PathUtils()

    def _power_state(self, userid, method, state):
        """Invoke xCAT REST API to set/get power state for a instance."""
        body = [state]
        url = self._xcat_url.rpower('/' + userid)
        with expect_invalid_xcat_node_and_reraise(userid):
            return xcat_request(method, url, body)

    def guest_start(self, userid):
        """"Power on VM."""
        try:
            self._power_state(userid, "PUT", "on")
        except exception.ZVMXCATInternalError as err:
            err_str = err.format_message()
            if ("Return Code: 200" in err_str and
                    "Reason Code: 8" in err_str):
                # VM already active
                LOG.warning("VM %s already active", userid)
                return
            else:
                raise

    def guest_stop(self, userid):
        self._power_state(userid, "PUT", "off")

    def guest_restart(self, userid):
        """Reboot instance"""
        self._power_state(userid, "PUT", "reboot")

    def guest_reset(self, userid):
        """Reset instance"""
        self._power_state(userid, "PUT", "reset")

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % userid)
        res_dict = self._power_state(userid, "GET", "stat")

        @wrap_invalid_xcat_resp_data_error
        def _get_power_string(d):
            tempstr = d['info'][0][0]
            return tempstr[(tempstr.find(':') + 2):].strip()

        return _get_power_string(res_dict)

    def get_host_info(self):
        """ Retrive host information"""
        host = CONF.zvm.host
        url = self._xcat_url.rinv('/' + host)
        inv_info_raw = xcat_request("GET", url)['info'][0]
        inv_keys = const.XCAT_RINV_HOST_KEYWORDS
        inv_info = translate_xcat_resp(inv_info_raw[0], inv_keys)

        hcp_hostname = inv_info['zhcp']
        self._zhcp_info = self._construct_zhcp_info(hcp_hostname)

        return inv_info

    def get_diskpool_info(self, pool):
        """Retrive diskpool info"""
        host = CONF.zvm.host
        addp = '&field=--diskpoolspace&field=' + pool
        url = self._xcat_url.rinv('/' + host, addp)
        res_dict = xcat_request("GET", url)

        dp_info_raw = res_dict['info'][0]
        dp_keys = const.XCAT_DISKPOOL_KEYWORDS
        dp_info = translate_xcat_resp(dp_info_raw[0], dp_keys)

        return dp_info

    def _get_hcp_info(self, hcp_hostname=None):
        """ Return a Dictionary containing zhcp's hostname,
        nodename and userid
        """
        if self._zhcp_info != {}:
            return self._zhcp_info
        else:
            if hcp_hostname is not None:
                return self._construct_zhcp_info(hcp_hostname)
            else:
                self.get_host_info()
                return self._zhcp_info

    def _construct_zhcp_info(self, hcp_hostname):
        hcp_node = hcp_hostname.partition('.')[0]
        return {'hostname': hcp_hostname,
                'nodename': hcp_node,
                'userid': self._get_userid_from_node(hcp_node)}

    def get_vm_list(self):
        zvm_host = CONF.zvm.host
        hcp_base = self._get_hcp_info()['hostname']

        url = self._xcat_url.tabdump("/zvm")
        res_dict = xcat_request("GET", url)

        vms = []

        with expect_invalid_xcat_resp_data(res_dict):
            data_entries = res_dict['data'][0][1:]
            for data in data_entries:
                l = data.split(",")
                node, hcp = l[0].strip("\""), l[1].strip("\"")
                hcp_short = hcp_base.partition('.')[0]

                # exclude zvm host and zhcp node from the list
                if (hcp.upper() == hcp_base.upper() and
                        node.upper() not in (zvm_host.upper(),
                        hcp_short.upper(), CONF.xcat.master_node.upper())):
                    vms.append(node)

        return vms

    @wrap_invalid_xcat_resp_data_error
    def _lsdef(self, userid):
        url = self._xcat_url.lsdef_node('/' + userid)
        resp_info = xcat_request("GET", url)['info'][0]
        return resp_info

    def image_performance_query(self, uid_list):
        """Call Image_Performance_Query to get guest current status.

        :uid_list: A list of zvm userids to be queried
        """
        if not isinstance(uid_list, list):
            uid_list = [uid_list]

        cmd = ('/opt/zhcp/bin/smcli Image_Performance_Query -T "%(uid_list)s" '
               '-c %(num)s' %
               {'uid_list': " ".join(uid_list), 'num': len(uid_list)})

        zhcp = self._get_hcp_info()['nodename']
        with expect_invalid_xcat_resp_data():
            resp = self.xdsh(zhcp, cmd)
            raw_data = resp["data"][0][0]

        ipq_kws = {
            'userid': "Guest name:",
            'guest_cpus': "Guest CPUs:",
            'used_cpu_time': "Used CPU time:",
            'elapsed_cpu_time': "Elapsed time:",
            'min_cpu_count': "Minimum CPU count:",
            'max_cpu_limit': "Max CPU limit:",
            'samples_cpu_in_use': "Samples CPU in use:",
            'samples_cpu_delay': ",Samples CPU delay:",
            'used_memory': "Used memory:",
            'max_memory': "Max memory:",
            'min_memory': "Minimum memory:",
            'shared_memory': "Shared memory:",
        }

        pi_dict = {}
        with expect_invalid_xcat_resp_data():
            rpi_list = raw_data.split(": \n")
            for rpi in rpi_list:
                try:
                    pi = translate_xcat_resp(rpi, ipq_kws)
                except exception.ZVMInvalidXCATResponseDataError as err:
                    emsg = err.format_message()
                    # when there is only one userid queried and this userid is
                    # in 'off'state, the smcli will only returns the queried
                    # userid number, no valid performance info returned.
                    if(emsg.__contains__("No value matched with keywords.")):
                        continue
                    else:
                        raise err
                for k, v in pi.items():
                    pi[k] = v.strip('" ')
                if pi.get('userid') is not None:
                    pi_dict[pi['userid']] = pi

        return pi_dict

    def get_image_performance_info(self, userid):
        pi_dict = self.image_performance_query([userid])
        return pi_dict.get(userid.upper(), None)

    def virtual_network_vswitch_query_iuo_stats(self):
        hcp_info = self._get_hcp_info()
        zhcp_userid = hcp_info['userid']
        zhcp_node = hcp_info['nodename']
        cmd = ('/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Query_IUO_Stats '
               '-T "%s" -k "switch_name=*"' % zhcp_userid)

        with expect_invalid_xcat_resp_data():
            resp = self.xdsh(zhcp_node, cmd)
            raw_data_list = resp["data"][0]

        while raw_data_list.__contains__(None):
            raw_data_list.remove(None)

        # Insert a blank line between two vswitch section in response data
        for rd in raw_data_list:
            if ' vswitch number: ' in rd.split('\n')[0]:
                # Which means a new vswitch section begin
                idx = raw_data_list.index(rd)
                if idx > 0:
                    # Insert a blank line
                    raw_data_list[idx - 1] += '\n '

        raw_data = '\n'.join(raw_data_list)
        rd_list = raw_data.split('\n')

        def _parse_value(data_list, idx, keyword, offset):
            return idx + offset, data_list[idx].rpartition(keyword)[2].strip()

        vsw_dict = {}
        with expect_invalid_xcat_resp_data():
            # vswitch count
            idx = 0
            idx, vsw_count = _parse_value(rd_list, idx, 'vswitch count:', 2)
            vsw_dict['vswitch_count'] = int(vsw_count)

            # deal with each vswitch data
            vsw_dict['vswitches'] = []
            for i in range(vsw_dict['vswitch_count']):
                vsw_data = {}
                # skip vswitch number
                idx += 1
                # vswitch name
                idx, vsw_name = _parse_value(rd_list, idx, 'vswitch name:', 1)
                vsw_data['vswitch_name'] = vsw_name
                # uplink count
                idx, up_count = _parse_value(rd_list, idx, 'uplink count:', 1)
                # skip uplink data
                idx += int(up_count) * 9
                # skip bridge data
                idx += 8
                # nic count
                vsw_data['nics'] = []
                idx, nic_count = _parse_value(rd_list, idx, 'nic count:', 1)
                nic_count = int(nic_count)
                for j in range(nic_count):
                    nic_data = {}
                    idx, nic_id = _parse_value(rd_list, idx, 'nic_id:', 1)
                    userid, toss, vdev = nic_id.partition(' ')
                    nic_data['userid'] = userid
                    nic_data['vdev'] = vdev
                    idx, nic_data['nic_fr_rx'] = _parse_value(rd_list, idx,
                                                              'nic_fr_rx:', 1
                                                              )
                    idx, nic_data['nic_fr_rx_dsc'] = _parse_value(rd_list, idx,
                                                            'nic_fr_rx_dsc:', 1
                                                            )
                    idx, nic_data['nic_fr_rx_err'] = _parse_value(rd_list, idx,
                                                            'nic_fr_rx_err:', 1
                                                            )
                    idx, nic_data['nic_fr_tx'] = _parse_value(rd_list, idx,
                                                              'nic_fr_tx:', 1
                                                              )
                    idx, nic_data['nic_fr_tx_dsc'] = _parse_value(rd_list, idx,
                                                            'nic_fr_tx_dsc:', 1
                                                            )
                    idx, nic_data['nic_fr_tx_err'] = _parse_value(rd_list, idx,
                                                            'nic_fr_tx_err:', 1
                                                            )
                    idx, nic_data['nic_rx'] = _parse_value(rd_list, idx,
                                                           'nic_rx:', 1
                                                           )
                    idx, nic_data['nic_tx'] = _parse_value(rd_list, idx,
                                                           'nic_tx:', 1
                                                           )
                    vsw_data['nics'].append(nic_data)
                # vlan count
                idx, vlan_count = _parse_value(rd_list, idx, 'vlan count:', 1)
                # skip vlan data
                idx += int(vlan_count) * 3
                # skip the blank line
                idx += 1

                vsw_dict['vswitches'].append(vsw_data)

        return vsw_dict

    @wrap_invalid_xcat_resp_data_error
    def _lsvm(self, userid):
        url = self._xcat_url.lsvm('/' + userid)
        with expect_invalid_xcat_node_and_reraise(userid):
            resp_info = xcat_request("GET", url)['info'][0][0]
        return resp_info.split('\n')

    def get_user_direct(self, userid):
        raw_dict = self._lsvm(userid)
        return [ent.partition(': ')[2] for ent in raw_dict]

    # TODO:moving to vmops and change name to ''
    def get_node_status(self, userid):
        url = self._xcat_url.nodestat('/' + userid)
        res_dict = xcat_request("GET", url)
        return res_dict

    def create_vm(self, userid, cpu, memory, disk_list, profile):
        # Create node for the vm
        self.prepare_for_spawn(userid)
        profile = 'profile=%s' % profile

        body = [profile,
                'password=%s' % CONF.zvm.user_default_password,
                'cpu=%i' % cpu,
                'memory=%im' % memory,
                'privilege=%s' % const.ZVM_USER_DEFAULT_PRIVILEGE]

#         # TODO: add it until xcat support it
#         if not CONF.zvm.zvm_default_admin_userid:
#             body.append('password=LBYONLY')
#         else:
#             body.append('password=LBYONLY')
#             body.append('logonby=%s' % CONF.zvm.zvm_default_admin_userid)

        if disk_list is None:
            disk_list = []

        ipl_disk = None
        if disk_list and 'is_boot_disk' in disk_list[0]:
            ipl_disk = CONF.zvm.user_root_vdev

        if ipl_disk:
            body.append('ipl=%s' % ipl_disk)

        url = self._xcat_url.mkvm('/' + userid)
        with expect_xcat_call_failed_and_reraise(
            exception.ZVMXCATCreateUserIdFailed, userid=userid):
            xcat_request("POST", url, body)

        if disk_list:
            # Add disks for vm
            self.add_mdisks(userid, disk_list)

    def add_mdisks(self, userid, disk_list, start_vdev=None):
        """Add disks for the userid

        :disks: A list dictionary to describe disk info, for example:
                disk: [{'size': '1g',
                       'format': 'ext3',
                       'disk_pool': 'ECKD:eckdpool1'}]

        """

        for idx, disk in enumerate(disk_list):
            vdev = self.generate_disk_vdev(start_vdev=start_vdev, offset=idx)
            self._add_mdisk(userid, disk, vdev)

    def _add_mdisk(self, userid, disk, vdev):
        """Create one disk for userid

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """

        size = disk['size']
        fmt = disk.get('format')
        disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
        diskpool_name = disk_pool.split(':')[1]

        if (disk_pool.split(':')[0].upper() == 'ECKD'):
            action = '--add3390'
        else:
            action = '--add9336'

        if fmt:
            body = [" ".join([action, diskpool_name, vdev, size, "MR", "''",
                    "''", "''", fmt])]
        else:
            body = [" ".join([action, diskpool_name, vdev, size])]

        url = get_xcat_url().chvm('/' + userid)
        with expect_xcat_call_failed_and_reraise(
            exception.ZVMXCATCreateUserIdFailed, userid=userid):
            xcat_request("PUT", url, body)

    # TODO:moving to vmops and change name to 'create_vm_node'
    def create_xcat_node(self, userid):
        """Create xCAT node for z/VM instance."""
        LOG.debug("Creating xCAT node for %s" % userid)
        hcp_hostname = self._get_hcp_info()['hostname']
        body = ['userid=%s' % userid,
                'hcp=%s' % hcp_hostname,
                'mgt=zvm',
                'groups=%s' % const.ZVM_XCAT_GROUP]
        url = self._xcat_url.mkdef('/' + userid)
        with expect_xcat_call_failed_and_reraise(
            exception.ZVMXCATCreateNodeFailed, node=userid):
            xcat_request("POST", url, body)

    # xCAT client can something special for xCAT here
    def prepare_for_spawn(self, userid):
        self.create_xcat_node(userid)

    def remove_image_file(self, image_name):
        url = self._xcat_url.rmimage('/' + image_name)
        xcat_request("DELETE", url)

    def remove_image_definition(self, image_name):
        url = self._xcat_url.rmobject('/' + image_name)
        xcat_request("DELETE", url)

    def change_vm_ipl_state(self, userid, ipl_state):
        body = ["--setipl %s" % ipl_state]
        url = get_xcat_url().chvm('/' + userid)
        xcat_request("PUT", url, body)

    def change_vm_fmt(self, userid, fmt, action, diskpool, vdev, size):
        if fmt:
            body = [" ".join([action, diskpool, vdev, size, "MR", "''", "''",
                    "''", fmt])]
        else:
            body = [" ".join([action, diskpool, vdev, size])]
        url = get_xcat_url().chvm('/' + userid)
        xcat_request("PUT", url, body)

    def get_tabdump_info(self):
        url = self._xcat_url.tabdump("/zvm")
        res_dict = xcat_request("GET", url)
        return res_dict

    def do_capture(self, nodename, profile):
        url = self._xcat_url.capture()
        body = ['nodename=' + nodename,
                'profile=' + profile]
        res = xcat_request("POST", url, body)
        return res

    def _clean_network_resource(self, userid):
        """Clean node records in xCAT mac, host and switch table."""
        self._delete_mac(userid)
        self._delete_switch(userid)
        self._delete_host(userid)

    def _delete_mac(self, userid):
        """Remove node mac record from xcat mac table."""
        commands = "-d node=%s mac" % userid
        url = self._xcat_url.tabch("/mac")
        body = [commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return xcat_request("PUT", url, body)['data']

    def _delete_host(self, userid):
        """Remove xcat hosts table rows where node name is node_name."""
        commands = "-d node=%s hosts" % userid
        body = [commands]
        url = self._xcat_url.tabch("/hosts")

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return xcat_request("PUT", url, body)['data']

    def _delete_switch(self, userid):
        """Remove node switch record from xcat switch table."""
        commands = "-d node=%s switch" % userid
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return xcat_request("PUT", url, body)['data']

    def create_nic(self, userid, vdev=None, nic_id=None,
                   mac_addr=None, ip_addr=None, active=False):
        ports_info = self._get_nic_ids()
        vdev_info = []
        for p in ports_info:
            target_user = p.split(',')[0].strip('"')
            used_vdev = p.split(',')[4].strip('"')
            if target_user == userid:
                vdev_info.append(used_vdev)

        if len(vdev_info) == 0:
            # no nic defined for the guest
            if vdev is None:
                nic_vdev = CONF.zvm.default_nic_vdev
            else:
                nic_vdev = vdev
        else:
            if vdev is None:
                used_vdev = max(vdev_info)
                nic_vdev = str(hex(int(used_vdev, 16) + 3))[2:]
            else:
                if self._is_vdev_valid(vdev, vdev_info):
                    nic_vdev = vdev
                else:
                    raise exception.ZVMInvalidInput(
                        msg=("The specified virtual device number "
                             "has already been used"))
        if len(nic_vdev) > 4:
            raise exception.ZVMNetworkError(
                        msg=("Virtual device number is not valid"))

        zhcpnode = self._get_hcp_info()['nodename']
        LOG.debug('Nic attributes: vdev is %(vdev)s, '
                  'ID is %(id)s, address is %(address)s',
                  {'vdev': nic_vdev,
                   'id': nic_id and nic_id or 'not specified',
                   'address': mac_addr and mac_addr or 'not specified'})
        self._create_nic(userid, nic_vdev, zhcpnode, nic_id=nic_id,
                         mac_addr=mac_addr, active=active)

        if ip_addr is not None:
            self._preset_vm_network(userid, ip_addr)

        return nic_vdev

    def _is_vdev_valid(self, vdev, vdev_info):
        for used_vdev in vdev_info:
            max_used_vdev = str(hex(int(used_vdev, 16) + 2))[2:]
            if ((int(vdev, 16) >= int(used_vdev, 16)) and
                (int(vdev, 16) <= int(max_used_vdev, 16))):
                return False

        return True

    def _create_nic(self, userid, vdev, zhcpnode, nic_id=None, mac_addr=None,
                    active=False):
        zhcp = self._get_hcp_info()['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Create_Extended_DM',
                             "-T %s" % userid,
                             "-k image_device_number=%s" % vdev,
                             "-k adapter_type=QDIO"))
        if mac_addr is not None:
            mac = ''.join(mac_addr.split(':'))[6:]
            commands += ' -k mac_id=%s' % mac
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMNetworkError(
                    msg=("Failed to create nic %s for %s in "
                         "the guest's user direct, %s") %
                         (vdev, userid, result['data'][0]))

        if active:
            if mac_addr is not None:
                LOG.warning("Ignore the mac address %s when "
                            "adding nic on an active system" % mac_addr)
            commands = ' '.join(('/opt/zhcp/bin/smcli',
                                 'Virtual_Network_Adapter_Create_Extended',
                                 "-T %s" % userid,
                                 "-k image_device_number=%s" % vdev,
                                 "-k adapter_type=QDIO"))
            xdsh_commands = 'command=%s' % commands
            body = [xdsh_commands]
            with expect_xcat_call_failed_and_reraise(
                    exception.ZVMNetworkError):
                result = xcat_request("PUT", url, body)
                if (result['errorcode'][0][0] != '0'):
                    persist_OK = False
                    commands = ' '.join((
                        '/opt/zhcp/bin/smcli',
                        'Virtual_Network_Adapter_Delete_DM',
                        '-T %s' % userid,
                        '-v %s' % vdev))
                    xdsh_commands = 'command=%s' % commands
                    body = [xdsh_commands]
                    with expect_xcat_call_failed_and_reraise(
                            exception.ZVMNetworkError):
                        del_rc = xcat_request("PUT", url, body)
                        if (del_rc['errorcode'][0][0] != '0'):
                            emsg = del_rc['data'][0][0]
                            if (emsg.__contains__("Return Code: 404") and
                                emsg.__contains__("Reason Code: 8")):
                                persist_OK = True
                            else:
                                persist_OK = False
                        else:
                            persist_OK = True
                    if persist_OK:
                        msg = ("Failed to create nic %s for %s on the active "
                               "guest system, %s") % (vdev, userid,
                                                      result['data'][0])
                    else:
                        msg = ("Failed to create nic %s for %s on the active "
                               "guest system, %s, and failed to revoke user "
                               "direct's changes, %s") % (vdev, userid,
                                                          result['data'][0],
                                                          del_rc['data'][0])

                    raise exception.ZVMNetworkError(msg)

        self._add_switch_table_record(userid, vdev, nic_id=nic_id,
                                      zhcp=zhcpnode)

    def _add_switch_table_record(self, userid, interface, nic_id=None,
                                 zhcp=None):
        """Add node name and nic name address into xcat switch table."""
        commands = ' '.join(("switch.node=%s" % userid,
                             "switch.interface=%s" % interface))
        if nic_id is not None:
            commands += " switch.port=%s" % nic_id
        if zhcp is not None:
            commands += " switch.comments=%s" % zhcp
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return xcat_request("PUT", url, body)['data']

    def delete_nic(self, userid, vdev, active=False):
        zhcp = self._get_hcp_info()['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)

        commands = ' '.join((
            '/opt/zhcp/bin/smcli '
            'Virtual_Network_Adapter_Delete_DM -T %s' % userid,
            '-v %s' % vdev))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                emsg = result['data'][0][0]
                if (emsg.__contains__("Return Code: 404") and
                    emsg.__contains__("Reason Code: 8")):
                    LOG.warning("Virtual device %s does not exist in "
                                "the guest's user direct", vdev)
                else:
                    raise exception.ZVMNetworkError(
                        msg=("Failed to delete nic %s for %s in "
                             "the guest's user direct, %s") %
                             (vdev, userid, result['data'][0]))

        self._delete_nic_from_switch(userid, vdev)
        if active:
            commands = ' '.join((
                '/opt/zhcp/bin/smcli '
                'Virtual_Network_Adapter_Delete -T %s' % userid,
                '-v %s' % vdev))
            xdsh_commands = 'command=%s' % commands
            body = [xdsh_commands]

            with expect_xcat_call_failed_and_reraise(
                    exception.ZVMNetworkError):
                result = xcat_request("PUT", url, body)
                if (result['errorcode'][0][0] != '0'):
                    emsg = result['data'][0][0]
                    if (emsg.__contains__("Return Code: 204") and
                        emsg.__contains__("Reason Code: 8")):
                        LOG.warning("Virtual device %s does not exist on "
                                    "the active guest system", vdev)
                    else:
                        raise exception.ZVMNetworkError(
                            msg=("Failed to delete nic %s for %s on "
                                 "the active guest system, %s") %
                                 (vdev, userid, result['data'][0]))

    def _delete_nic_from_switch(self, userid, vdev):
        """Remove node switch record from xcat switch table."""
        commands = "-d node=%s,interface=%s switch" % (userid, vdev)
        url = self._xcat_url.tabch("/switch")
        body = [commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            return xcat_request("PUT", url, body)['data']

    def _update_vm_info(self, node, node_info):
        """node_info looks like : ['sles12', 's390x', 'netboot',
        '0a0c576a_157f_42c8_bde5_2a254d8b77f']
        """
        url = self._xcat_url.chtab('/' + node)
        body = ['noderes.netboot=%s' % const.HYPERVISOR_TYPE,
                'nodetype.os=%s' % node_info[0],
                'nodetype.arch=%s' % node_info[1],
                'nodetype.provmethod=%s' % node_info[2],
                'nodetype.profile=%s' % node_info[3]]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMXCATUpdateNodeFailed, node=node):
            xcat_request("PUT", url, body)

    def guest_deploy(self, node, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        """image_name format looks like:
        sles12-s390x-netboot-0a0c576a_157f_42c8_bde5_2a254d8b77fc"""
        # Update node info before deploy
        node_info = image_name.split('-')
        self._update_vm_info(node, node_info)

        # Deploy the image to node
        url = self._xcat_url.nodeset('/' + node)
        vdev = vdev or CONF.zvm.user_root_vdev
        body = ['netboot',
                'device=%s' % vdev,
                'osimage=%s' % image_name]

        if transportfiles:
            body.append('transport=%s' % transportfiles)
        if remotehost:
            body.append('remotehost=%s' % remotehost)

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMXCATDeployNodeFailed, node=node):
            xcat_request("PUT", url, body)

    def check_space_imgimport_xcat(self, tar_file, xcat_free_space_threshold,
                                   zvm_xcat_master):
        pass

    def export_image(self, image_file_path):
        pass

    def image_import(self, image_file_path, os_version, remote_host=None):
        """import a spawn image to XCAT"""
        LOG.debug("Getting a spawn image...")
        image_uuid = image_file_path.split('/')[-1]
        disk_file_name = CONF.zvm.user_root_vdev + '.img'
        spawn_path = self._pathutils.get_spawn_folder()

        time_stamp_dir = self._pathutils.make_time_stamp()
        bundle_file_path = self._pathutils.get_bundle_tmp_path(time_stamp_dir)

        image_meta = {
                u'id': image_uuid,
                u'properties': {u'image_type_xcat': u'linux',
                               u'os_version': os_version,
                               u'os_name': u'Linux',
                               u'architecture': u's390x',
                               u'provision_method': u'netboot'}
                }

        # Generate manifest.xml
        LOG.debug("Generating the manifest.xml as a part of bundle file for "
                    "image %s", image_meta['id'])
        self.generate_manifest_file(image_meta, disk_file_name,
                                    bundle_file_path)
        # Generate the image bundle
        LOG.debug("Generating bundle file for image %s", image_meta['id'])
        image_bundle_package = self.generate_image_bundle(
                                    spawn_path, time_stamp_dir,
                                    disk_file_name, image_file_path)

        # Import image bundle to xCAT MN's image repository
        LOG.debug("Importing the image %s to xCAT", image_meta['id'])
        profile_str = image_uuid.replace('-', '_')
        image_profile = profile_str
        self.check_space_imgimport_xcat(image_bundle_package,
                        CONF.xcat.free_space_threshold,
                        CONF.xcat.master_node)

        # Begin to import
        body = ['osimage=%s' % image_bundle_package,
                'profile=%s' % image_profile,
                'nozip']
        xcat_server_ip = CONF.xcat.server
        if remote_host and remote_host.split('@')[-1] != xcat_server_ip:
            body.append('remotehost=%s' % remote_host)
        url = self._xcat_url.imgimport()

        try:
            xcat_request("POST", url, body)
        except (exception.ZVMXCATRequestFailed,
                exception.ZVMInvalidXCATResponseDataError,
                exception.ZVMXCATInternalError) as err:
            msg = ("Import the image bundle to xCAT MN failed: %s" %
                   err.format_message())
            raise exception.ZVMImageError(msg=msg)
        finally:
            os.remove(image_bundle_package)

    def get_vm_nic_vswitch_info(self, vm_id):
        """
        Get NIC and switch mapping for the specified virtual machine.
        """
        url = self._xcat_url.tabdump("/switch")
        with expect_invalid_xcat_resp_data():
            switch_info = xcat_request("GET", url)['data'][0]
            switch_info.pop(0)
            switch_dict = {}
            for item in switch_info:
                switch_list = item.split(',')
                if switch_list[0].strip('"') == vm_id:
                    switch_dict[switch_list[4].strip('"')] = \
                                            switch_list[1].strip('"')

            LOG.debug("Switch info the %(vm_id)s is %(switch_dict)s",
                      {"vm_id": vm_id, "switch_dict": switch_dict})
            return switch_dict

    def _add_host_table_record(self, vm_id, ip, host_name):
        """Add/Update hostname/ip bundle in xCAT MN nodes table."""
        commands = ' '.join(("node=%s" % vm_id,
                             "hosts.ip=%s" % ip,
                             "hosts.hostnames=%s" % host_name))
        body = [commands]
        url = self._xcat_url.tabch("/hosts")

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            xcat_request("PUT", url, body)['data']

    def _makehost(self):
        """Update xCAT MN /etc/hosts file."""
        url = self._xcat_url.network("/makehosts")
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            xcat_request("PUT", url)['data']

    def _preset_vm_network(self, vm_id, ip_addr):
        LOG.debug("Add ip/host name on xCAT MN for instance %s",
                  vm_id)

        self._add_host_table_record(vm_id, ip_addr, vm_id)
        self._makehost()

    def _get_nic_ids(self):
        addp = ''
        url = self._xcat_url.tabdump("/switch", addp)
        with expect_invalid_xcat_resp_data():
            nic_settings = xcat_request("GET", url)['data'][0]
        # remove table header
        nic_settings.pop(0)
        # it's possible to return empty array
        return nic_settings

    def _get_userid_from_node(self, vm_id):
        addp = '&col=node&value=%s&attribute=userid' % vm_id
        url = self._xcat_url.gettab("/zvm", addp)
        with expect_invalid_xcat_resp_data():
            return xcat_request("GET", url)['data'][0][0]

    def _get_nic_settings(self, port_id, field=None, get_node=False):
        """Get NIC information from xCat switch table."""
        LOG.debug("Get nic information for port: %s", port_id)
        addp = '&col=port&value=%s' % port_id + '&attribute=%s' % (
                                                field and field or 'node')
        url = self._xcat_url.gettab("/switch", addp)
        with expect_invalid_xcat_resp_data():
            ret_value = xcat_request("GET", url)['data'][0][0]
        if field is None and not get_node:
            ret_value = self._get_userid_from_node(ret_value)
        return ret_value

    def _get_node_from_port(self, port_id):
        return self._get_nic_settings(port_id, get_node=True)

    def grant_user_to_vswitch(self, vswitch_name, userid):
        """Set vswitch to grant user."""
        hcp_info = self._get_hcp_info()
        zhcp_userid = hcp_info['userid']
        zhcp = hcp_info['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % zhcp_userid,
            "-k switch_name=%s" % vswitch_name,
            "-k grant_userid=%s" % userid,
            "-k persist=YES"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMNetworkError(
                    msg=("Failed to grant user %s to vswitch %s, %s") %
                        (userid, vswitch_name, result['data'][0][0]))

    def revoke_user_from_vswitch(self, vswitch_name, userid):
        """Revoke user for vswitch."""
        hcp_info = self._get_hcp_info()
        zhcp_userid = hcp_info['userid']
        zhcp = hcp_info['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)

        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % zhcp_userid,
            "-k switch_name=%s" % vswitch_name,
            "-k revoke_userid=%s" % userid,
            "-k persist=YES"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMNetworkError(
                    msg=("Failed to revoke user %s from vswitch %s, %s") %
                        (userid, vswitch_name, result['data'][0][0]))

    def _couple_nic(self, userid, vdev, vswitch_name,
                    active=False):
        """Couple NIC to vswitch by adding vswitch into user direct."""
        zhcp = self._get_hcp_info()['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)

        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Connect_Vswitch_DM',
                             "-T %s" % userid,
                             "-v %s" % vdev,
                             "-n %s" % vswitch_name))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMNetworkError(
                    msg=("Failed to couple nic %s to vswitch %s "
                         "in the guest's user direct, %s") %
                         (vdev, vswitch_name, result['data'][0]))

        # the inst must be active, or this call will failed
        if active:
            commands = ' '.join(('/opt/zhcp/bin/smcli',
                                 'Virtual_Network_Adapter_Connect_Vswitch',
                                 "-T %s" % userid,
                                 "-v %s" % vdev,
                                 "-n %s" % vswitch_name))
            xdsh_commands = 'command=%s' % commands
            body = [xdsh_commands]
            with expect_xcat_call_failed_and_reraise(
                    exception.ZVMNetworkError):
                result = xcat_request("PUT", url, body)
                if (result['errorcode'][0][0] != '0'):
                    emsg = result['data'][0][0]
                    if (emsg.__contains__("Return Code: 204") and
                        emsg.__contains__("Reason Code: 20")):
                        LOG.warning("Virtual device %s already connected "
                                    "on the active guest system", vdev)
                    else:
                        persist_OK = False
                        commands = ' '.join((
                            '/opt/zhcp/bin/smcli',
                            'Virtual_Network_Adapter_Disconnect_DM',
                            '-T %s' % userid,
                            '-v %s' % vdev))
                        xdsh_commands = 'command=%s' % commands
                        body = [xdsh_commands]
                        with expect_xcat_call_failed_and_reraise(
                                exception.ZVMNetworkError):
                            dis_rc = xcat_request("PUT", url, body)
                            if (dis_rc['errorcode'][0][0] != '0'):
                                emsg = dis_rc['data'][0][0]
                                if (emsg.__contains__("Return Code: 212") and
                                    emsg.__contains__("Reason Code: 32")):
                                    persist_OK = True
                                else:
                                    persist_OK = False
                            else:
                                persist_OK = True
                        if persist_OK:
                            msg = ("Failed to couple nic %s to vswitch %s "
                                   "on the active guest system, %s") % (vdev,
                                            vswitch_name, result['data'][0])
                        else:
                            msg = ("Failed to couple nic %s to vswitch %s "
                                   "on the active guest system, %s, and "
                                   "failed to revoke user direct's changes, "
                                   "%s") % (vdev, vswitch_name,
                                            result['data'][0],
                                            dis_rc['data'][0])

                        raise exception.ZVMNetworkError(msg)

        """Update information in xCAT switch table."""
        self._update_xcat_switch(userid, vdev, vswitch_name)

    def couple_nic_to_vswitch(self, userid, nic_vdev,
                              vswitch_name, active=False):
        """Couple nic to vswitch."""
        LOG.debug("Connect nic to switch: %s", vswitch_name)
        self._couple_nic(userid, nic_vdev, vswitch_name, active=active)

    def _uncouple_nic(self, userid, vdev, active=False):
        """Uncouple NIC from vswitch"""
        zhcp = self._get_hcp_info()['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)

        commands = ' '.join(('/opt/zhcp/bin/smcli',
                             'Virtual_Network_Adapter_Disconnect_DM',
                             "-T %s" % userid,
                             "-v %s" % vdev))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                emsg = result['data'][0][0]
                if (emsg.__contains__("Return Code: 212") and
                    emsg.__contains__("Reason Code: 32")):
                    LOG.warning("Virtual device %s is already disconnected "
                                "in the guest's user direct", vdev)
                else:
                    raise exception.ZVMNetworkError(
                        msg=("Failed to uncouple nic %s "
                             "in the guest's user direct,  %s") %
                             (vdev, result['data'][0]))

        """Update information in xCAT switch table."""
        self._update_xcat_switch(userid, vdev, None)

        # the inst must be active, or this call will failed
        if active:
            commands = ' '.join(('/opt/zhcp/bin/smcli',
                                 'Virtual_Network_Adapter_Disconnect',
                                 "-T %s" % userid,
                                 "-v %s" % vdev))
            xdsh_commands = 'command=%s' % commands
            body = [xdsh_commands]
            with expect_xcat_call_failed_and_reraise(
                    exception.ZVMNetworkError):
                result = xcat_request("PUT", url, body)
                if (result['errorcode'][0][0] != '0'):
                    emsg = result['data'][0][0]
                    if (emsg.__contains__("Return Code: 204") and
                        emsg.__contains__("Reason Code: 48")):
                        LOG.warning("Virtual device %s is already "
                                    "disconnected on the active "
                                    "guest system", vdev)
                    else:
                        raise exception.ZVMNetworkError(
                            msg=("Failed to uncouple nic %s "
                                 "on the active guest system, %s") %
                                 (vdev, result['data'][0]))

    def uncouple_nic_from_vswitch(self, userid, nic_vdev,
                                  active=False):
        self._uncouple_nic(userid, nic_vdev, active=active)

    def _get_xcat_node_ip(self):
        addp = '&col=key&value=master&attribute=value'
        url = self._xcat_url.gettab("/site", addp)
        with expect_invalid_xcat_resp_data():
            return xcat_request("GET", url)['data'][0][0]

    def _get_xcat_node_name(self):
        if self._xcat_node_name is not None:
            return self._xcat_node_name

        xcat_ip = self._get_xcat_node_ip()
        addp = '&col=ip&value=%s&attribute=node' % (xcat_ip)
        url = self._xcat_url.gettab("/hosts", addp)
        with expect_invalid_xcat_resp_data():
            self._xcat_node_name = xcat_request(
                "GET", url)['data'][0][0]
            return self._xcat_node_name

    @wrap_invalid_xcat_resp_data_error
    def get_vswitch_list(self):
        hcp_info = self._get_hcp_info()
        userid = hcp_info['userid']
        zhcp = hcp_info['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Query',
            "-T %s" % userid,
            "-s \'*\'"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0' or not
                    result['data'] or not result['data'][0]):
                return None
            else:
                data = '\n'.join([s for s in result['data'][0]
                                if isinstance(s, unicode)])
                output = re.findall('VSWITCH:  Name: (.*)', data)
                return output

    @wrap_invalid_xcat_resp_data_error
    def add_vswitch(self, name, rdev=None, controller='*',
                    connection='CONNECT', network_type='IP',
                    router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                    gvrp='GVRP', queue_mem=8, native_vid=1, persist=True):
        hcp_info = self._get_hcp_info()
        userid = hcp_info['userid']
        zhcp = hcp_info['nodename']

        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Create_Extended',
            '-T %s' % userid,
            '-k switch_name=%s' % name))
        if rdev is not None:
            commands += " -k real_device_address" +\
                        "=\'%s\'" % rdev.replace(',', ' ')

        if controller != '*':
            commands += " -k controller_name=%s" % controller
        commands = ' '.join((commands,
                             "-k connection_value=%s" % connection,
                             "-k queue_memory_limit=%s" % queue_mem,
                             "-k transport_type=%s" % network_type,
                             "-k vlan_id=%s" % vid,
                             "-k persist=%s" % (persist and 'YES' or 'NO')))
        # Only if vswitch is vlan awared, port_type, gvrp and native_vid are
        # allowed to specified
        if isinstance(vid, int) or vid.upper() != 'UNAWARE':
            if ((native_vid is not None) and
                ((native_vid < 1) or (native_vid > 4094))):
                raise exception.ZVMInvalidInput(
                    msg=("Failed to create vswitch %s: %s") % (name,
                         'valid native VLAN id should be 1-4094 or None'))

            commands = ' '.join((commands,
                                 "-k port_type=%s" % port_type,
                                 "-k gvrp_value=%s" % gvrp,
                                 "-k native_vlanid=%s" % native_vid))

        if router is not None:
            commands += " -k routing_value=%s" % router

        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMNetworkError(
                    msg=("Failed to create vswitch %s: %s") %
                        (name, result['data']))

    def image_query(self, imagekeyword=None):
        """List the images"""
        if imagekeyword:
            imagekeyword = imagekeyword.replace('-', '_')
            parm = '&criteria=profile=~' + imagekeyword
        else:
            parm = None
        url = self._xcat_url.lsdef_image(addp=parm)
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMImageError):
            res = xcat_request("GET", url)
        image_list = []
        if res['info'] and 'Could not find' not in res['info'][0][0]:
            for img in res['info'][0]:
                image_name = img.strip().split(" ")[0]
                image_list.append(image_name)

        return image_list

    def get_user_console_output(self, userid, log_size):
        """get console log."""
        url = self._xcat_url.rinv('/' + userid, '&field=--consoleoutput'
                                  '&field=%s') % log_size

        # Because we might have logs in the console, we need ignore the warning
        res_info = xcat_request("GET", url)

        with expect_invalid_xcat_resp_data(res_info):
            log_data = res_info['info'][0][0]

        raw_log_list = log_data.split('\n')
        return '\n'.join([rec.partition(': ')[2] for rec in raw_log_list])

    def _generate_vdev(self, base, offset):
        """Generate virtual device number based on base vdev
        :param base: base virtual device number, string of 4 bit hex.
        :param offset: offset to base, integer.
        """
        vdev = hex(int(base, 16) + offset)[2:]
        return vdev.rjust(4, '0')

    def generate_disk_vdev(self, start_vdev=None, offset=0):
        """Generate virtual device number for disks
        :param offset: offset of user_root_vdev.
        :return: virtual device number, string of 4 bit hex.
        """
        if not start_vdev:
            start_vdev = CONF.zvm.user_root_vdev
        vdev = self._generate_vdev(start_vdev, offset)
        if offset >= 0 and offset < 254:
            return vdev
        else:
            msg = "Invalid virtual device number for disk:%s" % vdev
            LOG.error(msg)
            raise

    def _generate_disk_parmline(self, vdev, fmt, mntdir):
        parms = [
                'action=addMdisk',
                'vaddr=' + vdev,
                'filesys=' + fmt,
                'mntdir=' + mntdir
                ]
        parmline = ' '.join(parms)
        return parmline

    def process_additional_minidisks(self, userid, disk_info):
        """
        Generate and punch the scripts used to process additional disk into
        target vm's reader.
        """
        for idx, disk in enumerate(disk_info):
            vdev = disk.get('vdev') or self.generate_disk_vdev(
                                                    offset=(idx + 1))
            fmt = disk.get('format')
            mount_dir = disk.get('mntdir') or ''.join(['/mnt/', str(vdev)])
            disk_parms = self._generate_disk_parmline(vdev, fmt, mount_dir)
            self.aemod_handler(userid, const.DISK_FUNC_NAME, disk_parms)

    def aemod_handler(self, instance_name, func_name, parms):
        url = self._xcat_url.chvm('/' + instance_name)
        body = [" ".join(['--aemod', func_name, parms])]
        try:
            xcat_request("PUT", url, body)
        except Exception as err:
            emsg = err.format_message()
            LOG.error('Invoke AE method function: %(func)s on %(node)s '
                      'failed with reason: %(msg)s',
                      {'func': func_name, 'node': instance_name, 'msg': emsg})
            raise exception.ZVMSDKInternalError(msg=emsg)

    def delete_vm(self, userid):
        """Delete z/VM userid for the instance.This will remove xCAT node
        and network resource info at same time.
        """
        try:
            self._clean_network_resource(userid)
        except exception.ZVMNetworkError:
            LOG.warning("Clean MAC and VSWITCH failed in delete_userid")
        try:
            self.delete_userid(userid)
        except exception.ZVMXCATInternalError as err:
            emsg = err.format_message()
            if (emsg.__contains__("Return Code: 400") and
                    emsg.__contains__("Reason Code: 12")):
                # The vm was locked. Unlock before deleting
                self.unlock_userid(userid)
            elif (emsg.__contains__("Return Code: 408") and
                    emsg.__contains__("Reason Code: 12")):
                # The vm device was locked. Unlock the device before deleting
                self.unlock_devices(userid)
            else:
                LOG.debug("exception not able to handle in delete_userid "
                          "%s" % userid)
                raise err
            # delete the vm after unlock
            self.delete_userid(userid)
        except exception.ZVMXCATRequestFailed as err:
            emsg = err.format_message()
            if (emsg.__contains__("Invalid nodes and/or groups") and
                    emsg.__contains__("Forbidden")):
                # Assume neither zVM userid nor xCAT node exist in this case
                return
            else:
                raise err

    def delete_xcat_node(self, nodename):
        """Remove xCAT node for z/VM instance."""
        url = self._xcat_url.rmdef('/' + nodename)
        try:
            xcat_request("DELETE", url)
        except exception.ZVMXCATInternalError as err:
            if err.format_message().__contains__("Could not find an object"):
                # The xCAT node not exist
                return
            else:
                raise err

    def unlock_userid(self, userid):
        """Unlock the specified userid"""
        cmd = "/opt/zhcp/bin/smcli Image_Unlock_DM -T %s" % userid
        zhcp_node = self._get_hcp_info()['nodename']
        self.xdsh(zhcp_node, cmd)

    def unlock_devices(self, userid):
        cmd = "/opt/zhcp/bin/smcli Image_Lock_Query_DM -T %s" % userid
        zhcp_node = self._get_hcp_info()['nodename']
        resp = self.xdsh(zhcp_node, cmd)
        with expect_invalid_xcat_resp_data(resp):
            resp_str = resp['data'][0][0]

        if resp_str.__contains__("is Unlocked..."):
            # unlocked automatically, do nothing
            return

        def _unlock_device(vdev):
            cmd = ("/opt/zhcp/bin/smcli Image_Unlock_DM -T %(uid)s -v %(vdev)s"
                   % {'uid': userid, 'vdev': vdev})
            self.xdsh(zhcp_node, cmd)

        resp_list = resp_str.split('\n')
        for s in resp_list:
            if s.__contains__('Device address:'):
                vdev = s.rpartition(':')[2].strip()
                _unlock_device(vdev)

    def delete_userid(self, userid):
        url = self._xcat_url.rmvm('/' + userid)
        try:
            xcat_request("DELETE", url)
        except exception.ZVMXCATInternalError as err:
            emsg = err.format_message()
            LOG.debug("error emsg in delete_userid: %s", emsg)
            if (emsg.__contains__("Return Code: 400") and
                    emsg.__contains__("Reason Code: 4")):
                # zVM user definition not found, delete xCAT node directly
                self.delete_xcat_node(userid)
            else:
                raise err

    def _rewr(self, manifest_path):
        f = open(manifest_path + '/manifest.xml', 'r')
        lines = f.read()
        f.close()

        lines = lines.replace('\n', '')
        lines = re.sub(r'>(\s*)<', r'>\n\1<', lines)
        lines = re.sub(r'>[ \t]*(\S+)[ \t]*<', r'>\1<', lines)

        f = open(manifest_path + '/manifest.xml', 'w')
        f.write(lines)
        f.close()

    def generate_manifest_file(self, image_meta, disk_file_name,
                               manifest_path):
        """
        Generate the manifest.xml file from glance's image metadata
        as a part of the image bundle.
        """
        image_id = image_meta['id']
        image_type = image_meta['properties']['image_type_xcat']
        os_version = image_meta['properties']['os_version']
        os_name = image_meta['properties']['os_name']
        os_arch = image_meta['properties']['architecture']
        prov_method = image_meta['properties']['provision_method']

        image_profile = image_id.replace('-', '_')
        image_name_xcat = '-'.join((os_version, os_arch,
                               prov_method, image_profile))
        rootimgdir_str = ('/install', prov_method, os_version,
                          os_arch, image_profile)
        rootimgdir = '/'.join(rootimgdir_str)
        today_date = datetime.date.today()
        last_use_date_string = today_date.strftime("%Y-%m-%d")
        is_deletable = "auto:last_use_date:" + last_use_date_string

        doc = Dom.Document()
        xcatimage = doc.createElement('xcatimage')
        doc.appendChild(xcatimage)

        # Add linuximage section
        imagename = doc.createElement('imagename')
        imagename_value = doc.createTextNode(image_name_xcat)
        imagename.appendChild(imagename_value)
        rootimagedir = doc.createElement('rootimgdir')
        rootimagedir_value = doc.createTextNode(rootimgdir)
        rootimagedir.appendChild(rootimagedir_value)
        linuximage = doc.createElement('linuximage')
        linuximage.appendChild(imagename)
        linuximage.appendChild(rootimagedir)
        xcatimage.appendChild(linuximage)

        # Add osimage section
        osimage = doc.createElement('osimage')
        manifest = {'imagename': image_name_xcat,
                    'imagetype': image_type,
                    'isdeletable': is_deletable,
                    'osarch': os_arch,
                    'osname': os_name,
                    'osvers': os_version,
                    'profile': image_profile,
                    'provmethod': prov_method}

        if 'image_comments' in image_meta['properties']:
            manifest['comments'] = image_meta['properties']['image_comments']

        for item in list(manifest.keys()):
            itemkey = doc.createElement(item)
            itemvalue = doc.createTextNode(manifest[item])
            itemkey.appendChild(itemvalue)
            osimage.appendChild(itemkey)
            xcatimage.appendChild(osimage)
            f = open(manifest_path + '/manifest.xml', 'w')
            f.write(doc.toprettyxml(indent=''))
            f.close()

        # Add the rawimagefiles section
        rawimagefiles = doc.createElement('rawimagefiles')
        xcatimage.appendChild(rawimagefiles)

        files = doc.createElement('files')
        files_value = doc.createTextNode(rootimgdir + '/' + disk_file_name)
        files.appendChild(files_value)

        rawimagefiles.appendChild(files)

        f = open(manifest_path + '/manifest.xml', 'w')
        f.write(doc.toprettyxml(indent='  '))
        f.close()

        self._rewr(manifest_path)

        return manifest_path + '/manifest.xml'

    def generate_image_bundle(self, spawn_path, time_stamp_dir,
                              disk_file_name, image_file_path):
        """
        Generate the image bundle which is used to import to xCAT MN's
        image repository.
        """
        image_bundle_name = disk_file_name + '.tar'
        tar_file = spawn_path + '/' + time_stamp_dir + '_' + image_bundle_name
        LOG.debug("The generate the image bundle file is %s", tar_file)

        # copy tmp image file to bundle path
        bundle_file_path = self._pathutils.get_bundle_tmp_path(time_stamp_dir)
        image_file_copy = os.path.join(bundle_file_path, disk_file_name)
        shutil.copyfile(image_file_path, image_file_copy)

        os.chdir(spawn_path)
        tarFile = tarfile.open(tar_file, mode='w')
        try:
            tarFile.add(time_stamp_dir)
            tarFile.close()
        except Exception as err:
            msg = ("Generate image bundle failed: %s" % err)
            LOG.error(msg)
            if os.path.isfile(tar_file):
                os.remove(tar_file)
            raise exception.ZVMImageError(msg=msg)
        finally:
            self._pathutils.clean_temp_folder(time_stamp_dir)

        return tar_file

    def set_vswitch_port_vlan_id(self, vswitch_name, userid, vlan_id):
        hcp_info = self._get_hcp_info()
        zhcp_userid = hcp_info['userid']
        zhcp = hcp_info['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % zhcp_userid,
            "-k grant_userid=%s" % userid,
            "-k switch_name=%s" % vswitch_name,
            "-k user_vlan_id=%s" % vlan_id,
            "-k persist=YES"))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMNetworkError(
                    msg=("Failed to set vlan id for user %s, %s") %
                        (userid, result['data'][0][0]))

    def image_delete(self, image_name):
        try:
            self.remove_image_file(image_name)
            self.remove_image_definition(image_name)
        except exception.ZVMXCATInternalError as err:
            emsg = err.format_message()
            if (emsg.__contains__("Invalid image name")):
                LOG.info('The image %s does not exist in xCAT image'
                         ' repository' % image_name)

    def get_image_path_by_name(self, spawn_image_name):
        # eg. rhel7.2-s390x-netboot-<image_uuid>
        # eg. /install/netboot/rhel7.2/s390x/<image_uuid>/image_name.img
        name_split = spawn_image_name.split('-')
        # tmpdir can extract from 'tabdump site' but consume time
        tmpdir = '/install'
        """
        cmd = 'tabdump site'
        output = zvmtuils.execute(cmd)
        for i in output:
            if 'tmpdir' in i:
                tmpdir = i.split(',')[1]
        """
        image_uuid = name_split[-1]
        image_file_path = tmpdir + '/' + name_split[2] + '/' +\
                name_split[0] + '/' + name_split[1] + '/' + image_uuid +\
                '/' + CONF.zvm.user_root_vdev + '.img'
        return image_file_path

    def set_vswitch(self, switch_name, **kwargs):
        """Set vswitch"""
        set_vswitch_command = ["grant_userid", "user_vlan_id",
                               "revoke_userid", "real_device_address",
                               "port_name", "controller_name",
                               "connection_value", "queue_memory_limit",
                               "routing_value", "port_type", "persist",
                               "gvrp_value", "mac_id", "uplink",
                               "nic_userid", "nic_vdev",
                               "lacp", "interval", "group_rdev",
                               "iptimeout", "port_isolation", "promiscuous",
                               "MAC_protect", "VLAN_counters"]
        hcp_info = self._get_hcp_info()
        userid = hcp_info['userid']
        zhcp = hcp_info['nodename']
        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Set_Extended',
            "-T %s" % userid,
            "-k switch_name=%s" % switch_name))

        for k, v in kwargs.items():
            if k in set_vswitch_command:
                commands = ' '.join((commands,
                                     "-k %(key)s=\'%(value)s\'" %
                                     {'key': k, 'value': v}))
            else:
                raise exception.ZVMInvalidInput(
                    msg=("switch %s changes failed, invalid keyword %s") %
                    (switch_name, k))

        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                    raise exception.ZVMNetworkError(
                    msg=("switch %s changes failed, %s") %
                        (switch_name, result['data']))
        LOG.info('change vswitch %s done.' % switch_name)

    @wrap_invalid_xcat_resp_data_error
    def delete_vswitch(self, switch_name, persist=True):
        hcp_info = self._get_hcp_info()
        userid = hcp_info['userid']
        zhcp = hcp_info['nodename']

        url = self._xcat_url.xdsh("/%s" % zhcp)
        commands = ' '.join((
            '/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Delete_Extended',
            "-T %s" % userid,
            "-k switch_name=%s" % switch_name,
            "-k persist=%s" % (persist and 'YES' or 'NO')))
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]

        with expect_xcat_call_failed_and_reraise(
                exception.ZVMNetworkError):
            result = xcat_request("PUT", url, body)

            if (result['errorcode'][0][0] != '0'):
                emsg = result['data'][0][0]
                if (emsg.__contains__("Return Code: 212") and
                    emsg.__contains__("Reason Code: 40")):
                    LOG.warning("Vswitch %s does not exist", switch_name)
                    return
                else:
                    raise exception.ZVMNetworkError(
                    msg=("Failed to delete vswitch %s: %s") %
                        (switch_name, result['data']))

    def _update_xcat_switch(self, userid, nic_vdev, vswitch):
        """Update information in xCAT switch table."""
        if vswitch is not None:
            commands = ' '.join(("node=%s,interface=%s" % (userid, nic_vdev),
                                 "switch.switch=%s" % vswitch))
        else:
            commands = ' '.join(("node=%s,interface=%s" % (userid, nic_vdev),
                                 "switch.switch="))

        url = self._xcat_url.tabch("/switch")
        body = [commands]
        xcat_request("PUT", url, body)

    def run_commands_on_node(self, node, commands):
        url = self._xcat_url.xdsh("/%s" % node)
        xdsh_commands = 'command=%s' % commands
        body = [xdsh_commands]
        data = []
        with expect_xcat_call_failed_and_reraise(
                exception.ZVMException):
            result = xcat_request("PUT", url, body)
            if (result['errorcode'][0][0] != '0'):
                raise exception.ZVMException(
                    msg=("Failed to run command: %s on node %s, %s") %
                        (commands, node, result['errorcode'][0][0]))
            if (result['data'] and result['data'][0]):
                data = '\n'.join([s for s in result['data'][0]
                                if isinstance(s, unicode)])
                data = data.split('\n')
        return data

    def query_vswitch(self, switch_name):
        hcp_info = self._get_hcp_info()
        zhcp_userid = hcp_info['userid']
        zhcp_node = hcp_info['nodename']
        cmd = ('/opt/zhcp/bin/smcli Virtual_Network_Vswitch_Query_Extended '
               '-T "%s" -k "switch_name=%s"' % (zhcp_userid, switch_name))

        with expect_invalid_xcat_resp_data():
            resp = self.xdsh(zhcp_node, cmd)
            raw_data_list = resp["data"][0]

        while raw_data_list.__contains__(None):
            raw_data_list.remove(None)

        raw_data = '\n'.join(raw_data_list)
        rd_list = raw_data.split('\n')

        vsw_info = {}
        with expect_invalid_xcat_resp_data():
            # The first 21 lines contains the vswitch basic info
            # eg, name, type, port_type, vlan_awareness, etc
            idx_end = len(rd_list)
            for idx in range(21):
                rd = rd_list[idx].split(':')
                vsw_info[rd[1].strip()] = rd[2].strip()
            # Skip the vepa_status in line 22
            idx = 22

            def _parse_value(data_list, idx, keyword, offset=1):
                value = data_list[idx].rpartition(keyword)[2].strip()
                if value == '(NONE)':
                    value = 'NONE'
                return idx + offset, value

            # Start to analyse the real devices info
            vsw_info['real_devices'] = {}
            while((idx < idx_end) and
                  rd_list[idx].__contains__('real_device_address')):
                # each rdev has 6 lines' info
                idx, rdev_addr = _parse_value(rd_list, idx,
                                              'real_device_address: ')
                idx, vdev_addr = _parse_value(rd_list, idx,
                                              'virtual_device_address: ')
                idx, controller = _parse_value(rd_list, idx,
                                              'controller_name: ')
                idx, port_name = _parse_value(rd_list, idx, 'port_name: ')
                idx, dev_status = _parse_value(rd_list, idx,
                                                  'device_status: ')
                idx, dev_err = _parse_value(rd_list, idx,
                                            'device_error_status ')
                vsw_info['real_devices'][rdev_addr] = {'vdev': vdev_addr,
                                                'controller': controller,
                                                'port_name': port_name,
                                                'dev_status': dev_status,
                                                'dev_err': dev_err
                                                }
                # Under some case there would be an error line in the output
                # "Error controller_name is NULL!!", skip this line
                if ((idx < idx_end) and
                    rd_list[idx].__contains__(
                        'Error controller_name is NULL!!')):
                    idx += 1

            # Start to get the authorized userids
            vsw_info['authorized_users'] = {}
            while((idx < idx_end) and rd_list[idx].__contains__('port_num')):
                # each authorized userid has 6 lines' info at least
                idx, port_num = _parse_value(rd_list, idx,
                                              'port_num: ')
                idx, userid = _parse_value(rd_list, idx,
                                              'grant_userid: ')
                idx, prom_mode = _parse_value(rd_list, idx,
                                              'promiscuous_mode: ')
                idx, osd_sim = _parse_value(rd_list, idx, 'osd_sim: ')
                idx, vlan_count = _parse_value(rd_list, idx,
                                                  'vlan_count: ')
                vlan_ids = []
                for i in range(int(vlan_count)):
                    idx, id = _parse_value(rd_list, idx,
                                                  'user_vlan_id: ')
                    vlan_ids.append(id)
                # For vlan unaware vswitch, the query smcli would
                # return vlan_count as 1, here we just set the count to 0
                if (vsw_info['vlan_awareness'] == 'UNAWARE'):
                    vlan_count = 0
                    vlan_ids = []
                vsw_info['authorized_users'][userid] = {
                    'port_num': port_num,
                    'prom_mode': prom_mode,
                    'osd_sim': osd_sim,
                    'vlan_count': vlan_count,
                    'vlan_ids': vlan_ids
                    }

            # Start to get the connected adapters info
            # OWNER_VDEV would be used as the dict key for each adapter
            vsw_info['adapters'] = {}
            while((idx < idx_end) and
                  rd_list[idx].__contains__('adapter_owner')):
                # each adapter has four line info: owner, vdev, macaddr, type
                idx, owner = _parse_value(rd_list, idx,
                                              'adapter_owner: ')
                idx, vdev = _parse_value(rd_list, idx,
                                              'adapter_vdev: ')
                idx, mac = _parse_value(rd_list, idx,
                                              'adapter_macaddr: ')
                idx, type = _parse_value(rd_list, idx, 'adapter_type: ')
                key = owner + '_' + vdev
                vsw_info['adapters'][key] = {
                    'mac': mac,
                    'type': type
                    }
            # Todo: analyze and add the uplink NIC info and global member info

        return vsw_info

    def _get_vm_mgt_ip(self, vm_id):
        addp = '&col=node&value=%s&attribute=ip' % vm_id
        url = self._xcat_url.gettab("/hosts", addp)
        with expect_invalid_xcat_resp_data():
            return xcat_request("GET", url)['data'][0][0]

    def image_get_root_disk_size(self, image_name):
        """use 'hexdump' to get the root_disk_size."""
        image_file_path = self.get_image_path_by_name(image_name)

        cmd = 'hexdump -C -n 64 %s' % image_file_path
        with expect_invalid_xcat_resp_data():
            output = self.xdsh(CONF.xcat.master_node, cmd)['data'][0][0]
            output = output.replace(CONF.xcat.master_node + ': ', '')

        LOG.debug("hexdump result is %s", output)
        try:
            root_disk_size = output[144:156].strip()
        except ValueError:
            msg = ("Image file at %s is missing built-in disk size "
                    "metadata, it was probably not captured with xCAT"
                    % image_file_path)
            raise exception.ZVMImageError(msg=msg)

        if 'FBA' not in output and 'CKD' not in output:
            msg = ("The image's disk type is not valid. Currently we only"
                      " support FBA and CKD disk")
            raise exception.ZVMImageError(msg=msg)

        LOG.debug("The image's root_disk_size is %s", root_disk_size)
        return root_disk_size

    def get_xcat_version(self):
        """Return the version of xCAT."""
        url = get_xcat_url().version()
        with expect_invalid_xcat_resp_data():
            data = xcat_request('GET', url)['data']
            version = data[0][0].split()[1]
            version = version.strip()
            return version

    def xdsh(self, node, commands):
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

    def punch_file(self, node, fn, fclass):
        body = [" ".join(['--punchfile', fn, fclass, zvmutils.get_host()])]
        url = get_xcat_url().chvm('/' + node)

        try:
            xcat_request("PUT", url, body)
        except Exception as err:
            LOG.error('Punch file to %(node)s failed: %(msg)s' %
                          {'node': node, 'msg': err})
        finally:
            os.remove(fn)

    def punch_adminpass_file(self, temp_path, userid, admin_password,
                             linuxdist):
        adminpass_fn = ''.join([temp_path, '/adminpwd.sh'])
        self._generate_adminpass_file(adminpass_fn, admin_password, linuxdist)
        self.punch_file(userid, adminpass_fn, 'X')

    def _generate_adminpass_file(self, fn, admin_password, linuxdist):
        pwd_str = linuxdist.get_change_passwd_command(admin_password)
        lines = ['#!/bin/bash\n', pwd_str]
        with open(fn, 'w') as f:
            f.writelines(lines)

    def punch_xcat_auth_file(self, temp_path, userid):
        """Make xCAT MN authorized by virtual machines."""
        mn_pub_key = self.get_mn_pub_key()
        auth_fn = ''.join([temp_path, '/xcatauth.sh'])
        self._generate_auth_file(auth_fn, mn_pub_key)
        self.punch_file(userid, auth_fn, 'X')

    def get_mn_pub_key(self):
        cmd = 'cat /root/.ssh/id_rsa.pub'
        resp = self.xdsh(CONF.xcat.master_node, cmd)
        key = resp['data'][0][0]
        start_idx = key.find('ssh-rsa')
        key = key[start_idx:]
        return key

    def _generate_auth_file(self, fn, pub_key):
        lines = ['#!/bin/bash\n',
        'echo "%s" >> /root/.ssh/authorized_keys' % pub_key]
        with open(fn, 'w') as f:
            f.writelines(lines)

    @wrap_invalid_xcat_resp_data_error
    def create_xcat_mgt_network(self, mgt_vswitch):
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

    def get_xcat_url(self):
        return get_xcat_url()
