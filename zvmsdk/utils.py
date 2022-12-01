# Copyright 2017,2022 IBM Corp.
# Copyright 2013 NEC Corporation.
# Copyright 2011 OpenStack Foundation.
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
import errno
import functools
import inspect
import netaddr
import os
import pwd
import re
import shlex
import shutil
import six
import subprocess
import sys
import tempfile
import time
import traceback
import threading
import string

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import exception
from zvmsdk import log

CONF = config.CONF
LOG = log.LOG


def execute(cmd, timeout=None):
    """ execute command, return rc and output string.
    The cmd argument can be a string or a list composed of
    the command name and each of its argument.
    eg, ['/usr/bin/cp', '-r', 'src', 'dst'] """

    # Parse cmd string to a list
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)
    # Execute command
    rc = 0
    output = ""
    try:
        output = subprocess.check_output(cmd, close_fds=True,
                                         stderr=subprocess.STDOUT,
                                         timeout=timeout)
    except subprocess.CalledProcessError as err:
        rc = err.returncode
        output = err.output
    except (subprocess.TimeoutExpired,
            PermissionError) as err:
        raise err
    except Exception as err:
        err_msg = ('Command "%s" Error: %s' % (' '.join(cmd), str(err)))
        raise exception.SDKInternalError(msg=err_msg)

    output = bytes.decode(output)
    return (rc, output)


def get_host():
    return ''.join([pwd.getpwuid(os.geteuid()).pw_name, '@',
                    CONF.network.my_ip])


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
    except (IndexError, ValueError, KeyError, TypeError):
        errmsg = ("Invalid memory format: %s") % s
        raise exception.SDKInternalError(msg=errmsg)


class PathUtils(object):

    def clean_temp_folder(self, tmp_folder):
        if os.path.isdir(tmp_folder):
            LOG.debug('Removing existing folder %s ', tmp_folder)
            shutil.rmtree(tmp_folder)

    def _get_guest_path(self):
        return os.path.join(constants.SDK_DATA_PATH, 'guests')

    def mkdir_if_not_exist(self, folder):
        if not os.path.exists(folder):
            LOG.debug("Creating the guest path %s", folder)
            os.makedirs(folder)

    # This is for persistent info for guests
    # by default it's /var/lib/zvmsdk/guests/xxxx
    def remove_guest_path(self, userid):
        guest_folder = os.path.join(self._get_guest_path(), userid)
        try:
            shutil.rmtree(guest_folder)
        except Exception:
            # Ignore any exception for delete temp folder
            pass

    def get_guest_temp_path(self, userid):
        tmp_inst_dir = tempfile.mkdtemp(prefix=userid,
                                        dir='/tmp')
        return tmp_inst_dir

    def get_guest_path(self, userid):
        guest_folder = os.path.join(self._get_guest_path(), userid)
        self.mkdir_if_not_exist(guest_folder)
        return guest_folder

    def get_console_log_path(self, userid):
        return os.path.join(self.get_guest_path(userid), "console.log")

    def create_import_image_repository(self, image_osdistro, type,
                                       image_name):
        zvmsdk_image_import_repo = os.path.join(
                                    CONF.image.sdk_image_repository,
                                    type,
                                    image_osdistro,
                                    image_name)

        if not os.path.exists(zvmsdk_image_import_repo):
            LOG.debug('Creating image repository %s for image import',
                      zvmsdk_image_import_repo)
            os.makedirs(zvmsdk_image_import_repo)
        return zvmsdk_image_import_repo

    def create_file_repository(self, file_type):
        zvmsdk_file_repo = os.path.join(CONF.file.file_repository,
                                        file_type)

        if not os.path.exists(zvmsdk_file_repo):
            LOG.debug('Creating file repository %s for file transfer',
                      zvmsdk_file_repo)
            os.makedirs(zvmsdk_file_repo)
        return zvmsdk_file_repo


def to_utf8(text):
    if isinstance(text, bytes):
        return text
    elif isinstance(text, six.text_type):
        return text.encode()
    else:
        raise TypeError("bytes or Unicode expected, got %s"
                        % type(text).__name__)


def valid_userid(userid):
    if not isinstance(userid, six.string_types):
        return False
    if ((userid == '') or
        (userid.find(' ') != -1)):
        return False
    if len(userid) > 8:
        return False
    return True


def valid_mac_addr(addr):
    ''' Validates a mac address'''
    if not isinstance(addr, six.string_types):
        return False
    valid = re.compile(r'''
                      (^([0-9A-F]{2}[:]){5}([0-9A-F]{2})$)
                      ''',
                      re.VERBOSE | re.IGNORECASE)
    return valid.match(addr) is not None


def valid_cidr(cidr):
    if not isinstance(cidr, six.string_types):
        return False
    try:
        netaddr.IPNetwork(cidr)
    except netaddr.AddrFormatError:
        return False
    if '/' not in cidr:
        return False
    if re.search('\s', cidr):
        return False
    return True


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


def check_input_types(*types, **validkeys):
    """This is a function decorator to check all input parameters given to
    decorated function are in expected types.

    The checks can be skipped by specify skip_input_checks=True in decorated
    function.

    :param tuple types: expected types of input parameters to the decorated
                        function
    :param validkeys: valid keywords(str) in a list.
                      e.g. validkeys=['key1', 'key2']
    """
    def decorator(function):
        @functools.wraps(function)
        def wrap_func(*args, **kwargs):
            if args[0]._skip_input_check:
                # skip input check
                return function(*args, **kwargs)
            # drop class object self
            inputs = args[1:]
            if (len(inputs) > len(types)):
                msg = ("Too many parameters provided: %(specified)d specified,"
                       "%(expected)d expected." %
                       {'specified': len(inputs), 'expected': len(types)})
                LOG.info(msg)
                raise exception.SDKInvalidInputNumber(function.__name__,
                                                      len(types), len(inputs))

            argtypes = tuple(map(type, inputs))
            match_types = types[0:len(argtypes)]

            invalid_type = False
            invalid_userid_idx = -1
            for idx in range(len(argtypes)):
                _mtypes = match_types[idx]
                if not isinstance(_mtypes, tuple):
                    _mtypes = (_mtypes,)

                argtype = argtypes[idx]
                if constants._TUSERID in _mtypes:
                    userid_type = True
                    for _tmtype in _mtypes:
                        if ((argtype == _tmtype) and
                            (_tmtype != constants._TUSERID)):
                            userid_type = False
                    if (userid_type and
                        (not valid_userid(inputs[idx]))):
                        invalid_userid_idx = idx
                        break
                elif argtype not in _mtypes:
                    invalid_type = True
                    break

            if invalid_userid_idx != -1:
                msg = ("Invalid string value found at the #%d parameter, "
                       "length should be less or equal to 8 and should not be "
                       "null or contain spaces." % (invalid_userid_idx + 1))
                LOG.info(msg)
                raise exception.SDKInvalidInputFormat(msg=msg)

            if invalid_type:
                msg = ("Invalid input types: %(argtypes)s; "
                       "Expected types: %(types)s" %
                       {'argtypes': str(argtypes), 'types': str(types)})
                LOG.info(msg)
                raise exception.SDKInvalidInputTypes(function.__name__,
                                                     str(types), str(argtypes))

            valid_keys = validkeys.get('valid_keys')
            if valid_keys:
                for k in kwargs.keys():
                    if k not in valid_keys:
                        msg = ("Invalid keyword: %(key)s; "
                               "Expected keywords are: %(keys)s" %
                               {'key': k, 'keys': str(valid_keys)})
                        LOG.info(msg)
                        raise exception.SDKInvalidInputFormat(msg=msg)
            return function(*args, **kwargs)
        return wrap_func
    return decorator


def synchronized(lock_name):
    """Synchronization decorator.

    :param lock_name: (str) Lock name.

    Decorating a method like so::

        @synchronized('mylock')
        def foo(self, *args):
           ...

    ensures that only one thread will execute the foo method at a time.

    Different methods can share the same lock::

        @synchronized('mylock')
        def foo(self, *args):
           ...

        @synchronized('mylock')
        def bar(self, *args):
           ...

    This way only one of either foo or bar can be executing at a time.

    Lock name can be formatted using Python format string syntax::

        @synchronized('volumeAttachOrDetach-{connection_info[assigner_id]}')
        def attach(self, connection_info):
           ...
    """
    # meta_lock:
    # used for serializing concurrent threads to access lock_pool
    meta_lock = vars(synchronized).setdefault(
        '_meta_lock', threading.RLock())
    LOG.info('synchronized: meta_lock {}, current thread {}'.format(
        meta_lock, threading.current_thread().name))
    # concurrent_thread_count:
    # for each lock in lock_pool,
    # count the number of concurrent threads, including
    # the thread holding the lock, and the threads waiting for the lock
    concurrent_thread_count = vars(synchronized).setdefault(
        '_concurrent_thread_count', dict())
    # lock_pool:
    # store the locks with lock_name as key
    lock_pool = vars(synchronized).setdefault(
        '_lock_pool', dict())
    LOG.info('synchronized: lock_pool {}, current thread {}'.format(
        lock_pool, threading.current_thread().name))

    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            # Pre-process:
            # format lock_name
            call_args = inspect.getcallargs(func, *args, **kwargs)
            formatted_name = lock_name.format(**call_args)
            cur_thread = threading.current_thread()
            # create only one lock per formatted_name
            with meta_lock:
                if formatted_name not in lock_pool:
                    lock_pool[formatted_name] = threading.RLock()
                    concurrent_thread_count[formatted_name] = 1
                else:
                    concurrent_thread_count[formatted_name] += 1
            the_lock = lock_pool[formatted_name]
            # acquire the_lock
            LOG.info('synchronized: '
                     'acquiring lock {}, '
                     'concurrent thread count {}, '
                     'current thread: {}'.format(
                formatted_name,
                concurrent_thread_count[formatted_name],
                cur_thread.name))
            t1 = time.time()
            the_lock.acquire()
            t2 = time.time()
            LOG.info('synchronized: '
                     'acquired lock {}, '
                     'waited {:.2f} seconds, '
                     'current thread: {}'.format(
                formatted_name, t2 - t1, cur_thread.name))
            try:
                # Call decorated function
                return func(*args, **kwargs)
            finally:
                # release the_lock
                the_lock.release()
                t3 = time.time()
                LOG.info('synchronized: '
                         'released lock {}, '
                         'held {:.2f} seconds, '
                         'current thread: {}'.format(
                    formatted_name, t3 - t2, cur_thread.name))
                # Post-process:
                # delete/pop the lock if no concurrent thread for it
                with meta_lock:
                    if concurrent_thread_count[formatted_name] == 1:
                        lock_pool.pop(formatted_name)
                        concurrent_thread_count.pop(formatted_name)
                    else:
                        concurrent_thread_count[formatted_name] -= 1
                    LOG.info('synchronized: '
                             'after releasing lock {}, '
                             'concurrent thread count {}, '
                             'current thread: {}'.format(
                        formatted_name,
                        concurrent_thread_count.get(formatted_name, 0),
                        cur_thread.name))
        return _wrapper
    return _decorator


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    try:
        return getattr(sys.modules[mod_str], class_str)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                          (class_str,
                           traceback.format_exception(*sys.exc_info())))


def import_object(import_str, *args, **kwargs):
    """Import a class and return an instance of it."""
    return import_class(import_str)(*args, **kwargs)


@contextlib.contextmanager
def expect_invalid_resp_data(data=''):
    """Catch exceptions when using zvm client response data."""
    try:
        yield
    except (ValueError, TypeError, IndexError, AttributeError,
            KeyError) as err:
        msg = ('Invalid smt response data: %s. Error: %s' %
               (data, six.text_type(err)))
        LOG.error(msg)
        raise exception.SDKInternalError(msg=msg)


def wrap_invalid_resp_data_error(function):
    """Catch exceptions when using zvm client response data."""

    @functools.wraps(function)
    def decorated_function(*arg, **kwargs):
        try:
            return function(*arg, **kwargs)
        except (ValueError, TypeError, IndexError, AttributeError,
                KeyError) as err:
            msg = ('Invalid smt response data. Error: %s' %
                   six.text_type(err))
            LOG.error(msg)
            raise exception.SDKInternalError(msg=msg)

    return decorated_function


@contextlib.contextmanager
def expect_and_reraise_internal_error(modID='SDK'):
    """Catch all kinds of zvm client request failure and reraise.

    modID: the moduleID that the internal error happens in.
    """
    try:
        yield
    except exception.SDKInternalError as err:
        msg = err.format_message()
        raise exception.SDKInternalError(msg, modID=modID)


@contextlib.contextmanager
def log_and_reraise_sdkbase_error(action):
    """Catch SDK base exception and print error log before reraise exception.

    msg: the error message to be logged.
    """
    try:
        yield
    except exception.SDKBaseException:
        msg = "Failed to " + action + "."
        LOG.error(msg)
        raise


@contextlib.contextmanager
def log_and_reraise_smt_request_failed(action=None):
    """Catch SDK base exception and print error log before reraise exception.

    msg: the error message to be logged.
    """
    try:
        yield
    except exception.SDKSMTRequestFailed as err:
        msg = ''
        if action is not None:
            msg = "Failed to %s. " % action
        msg += "SMT error: %s" % err.format_message()
        LOG.error(msg)
        raise exception.SDKSMTRequestFailed(err.results, msg)


@contextlib.contextmanager
def ignore_errors():
    """Only execute the clauses and ignore the results"""
    try:
        yield
    except Exception as err:
        LOG.error('ignore an error: ' + str(err))
        pass


def get_smt_userid():
    """Get the userid of smt server"""
    cmd = ["sudo", "/sbin/vmcp", "query userid"]
    try:
        userid = subprocess.check_output(cmd,
                                         close_fds=True,
                                         stderr=subprocess.STDOUT)
        userid = bytes.decode(userid)
        userid = userid.split()[0]
        return userid
    except Exception as err:
        msg = ("Could not find the userid of the smt server: %s") % err
        raise exception.SDKInternalError(msg=msg)


def get_lpar_name():
    """Get the name of the LPAR that this vm is on."""
    cmd = ["sudo", "/sbin/vmcp", "query userid"]
    try:
        userid = subprocess.check_output(cmd,
                                         close_fds=True,
                                         stderr=subprocess.STDOUT)
        userid = bytes.decode(userid)
        userid = userid.split()[-1]
        return userid
    except Exception as err:
        msg = ("Failed to get the LPAR name for the smt server: %s") % err
        raise exception.SDKInternalError(msg=msg)


def get_namelist():
    """Generate namelist.

    Either through set CONF.zvm.namelist, or by generate based on smt userid.
    """
    if CONF.zvm.namelist is not None:
        # namelist length limit should be 64, but there's bug limit to 8
        # will change the limit to 8 once the bug fixed
        if len(CONF.zvm.namelist) <= 8:
            return CONF.zvm.namelist

    # return ''.join(('NL', get_smt_userid().rjust(6, '0')[-6:]))
    # py3 compatible changes
    userid = get_smt_userid()
    return 'NL' + userid.rjust(6, '0')[-6:]


def generate_iucv_authfile(fn, client):
    """Generate the iucv_authorized_userid file"""
    lines = ['#!/bin/bash\n',
             'echo -n %s > /etc/iucv_authorized_userid\n' % client]
    with open(fn, 'w') as f:
        f.writelines(lines)


def translate_response_data_to_expect_dict(results, step):
    """
    Translate SMT response to a python dictionary
    ['volume name: IASFBA', 'volume_type:9336-ET', 'volume_size:564718',
     'volume_name: IAS1CM', 'volume_type:3390-09', 'volume_size:60102']
     translate to:
     {'IASFBA': {'volume_type': '9336-ET', 'volume_size': '564718'},
      'IAS1CM': {'volume_type': '3390-09', 'volume_size': '60102'}}
    :results: the SMT response in list format
    :step: count list members converted to one member of the directory
    """
    data = {}
    for i in range(0, len(results), step):
        volume_name = results[i].split(':')[1].strip()
        data[volume_name] = {}
        for k in range(1, step):
            key, value = results[i + k].split(':')
            data[volume_name][key] = value
    return data


@wrap_invalid_resp_data_error
def translate_response_to_dict(rawdata, dirt):
    """Translate SMT response to a python dictionary.

    SMT response example:
    keyword1: value1\n
    keyword2: value2\n
    ...
    keywordn: valuen\n

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
        msg = ("Invalid smt response data. Error: No value matched with "
               "keywords. Raw Data: %(raw)s; Keywords: %(kws)s" %
               {'raw': rawdata, 'kws': str(dirt)})
        raise exception.SDKInternalError(msg=msg)

    return data


def make_dummy_image(image_path, d_type='CKD'):
    if d_type not in ('CKD', 'FBA'):
        d_type = 'CKD'

    d_unit = 'CYL'
    if d_type == 'FBA':
        d_unit = 'BLK'

    header = ("z/VM %(type)s Disk Image:           0 %(unit)s" %
              {'type': d_type, 'unit': d_unit})

    header = (' '.join((header, 'HLen: 0055', 'GZIP: 0')))
    with open(image_path, 'wb') as f:
        f.write(header.encode())


@contextlib.contextmanager
def acquire_lock(lock):
    """ lock wrapper """
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def check_userid_exist(userid, needLogon=False):
    """The successful output is: FBA0004  - DSC
    The successful output for device is (vmcp q 0100):
    DASD 0100 3390 IAS106 R/W      29128 CYL ON DASD  1356 SUBCHANNEL = 0003

    Errors are:
    HCPCQV003E Invalid option - XXXXX
    HCPQVD040E Device XXXX does not exist
    HCPCFC026E Operand missing or invalid
    HCPCQU045E XXXXX not logged on

    Success msgs:
    HCPCQU361E LOGOFF/FORCE pending for user xxxxxx
    """
    cmd = 'sudo vmcp q %s' % userid
    rc, output = execute(cmd)
    if needLogon:
        strfail = '(^HCP\w\w\w003E|^HCP\w\w\w040E|' + \
                    '^HCP\w\w\w026E|^HCP\w\w\w045E)'
        strok = '(^%s)' % userid
    else:
        strfail = '(^HCP\w\w\w003E|^HCP\w\w\w040E|^HCP\w\w\w026E)'
        strok = '(^%s|^HCP\w\w\w045E|^HCP\w\w\w361E)' % userid

    if re.search(strfail, output):
        # userid not exist
        return False
    if re.search(strok, output):
        # userid exist
        return True
    # When reaching here most likely the userid represents a device
    # and anyway it's not a guest.
    return False


def check_userid_on_others(userid):
    try:
        check_userid_exist(userid)
        cmd = 'sudo vmcp q %s' % userid
        rc, output = execute(cmd)
        if re.search(' - SSI', output):
            return True
        return False
    except Exception as err:
        msg = ("Could not find the userid: %s") % err
        raise exception.SDKInternalError(msg=msg)


def expand_fcp_list(fcp_list):
    """Expand fcp list string into a python list object which contains
    each fcp devices in the list string. A fcp list is composed of fcp
    device addresses, range indicator '-', and split indicator ';'.

    Example 1:
    if fcp_list is "0011-0013;0015;0017-0018",
    then the function will return
    {
      0: {'0011' ,'0012', '0013'}
      1: {'0015'}
      2: {'0017', '0018'}
    }

    Example 2:
    if fcp_list is empty string: '',
    then the function will return an empty set: {}

    ATTENTION: To support multipath, we expect fcp_list should be like
    "0011-0014;0021-0024", "0011-0014" should have been on same physical
    WWPN which we called path0, "0021-0024" should be on another physical
    WWPN we called path1 which is different from "0011-0014".
    path0 and path1 should have same count of FCP devices in their group.
    When attach, we will choose one WWPN from path0 group, and choose
    another one from path1 group. Then we will attach this pair of WWPNs
    together to the guest as a way to implement multipath.
    """
    LOG.debug("Expand FCP list %s" % fcp_list)

    if not fcp_list:
        return dict()
    fcp_list = fcp_list.strip()
    fcp_list = fcp_list.replace(' ', '')
    range_pattern = '[0-9a-fA-F]{1,4}(-[0-9a-fA-F]{1,4})?'
    match_pattern = "^(%(range)s)(;%(range)s;?)*$" % \
                    {'range': range_pattern}

    item_pattern = "(%(range)s)(,%(range)s?)*" % \
                   {'range': range_pattern}

    multi_match_pattern = "^(%(range)s)(;%(range)s;?)*$" % \
                   {'range': item_pattern}

    if not re.match(match_pattern, fcp_list) and \
       not re.match(multi_match_pattern, fcp_list):
        errmsg = ("Invalid FCP address %s") % fcp_list
        raise exception.SDKInternalError(msg=errmsg)

    fcp_devices = {}
    path_no = 0
    for _range in fcp_list.split(';'):
        for item in _range.split(','):
            # remove duplicate entries
            devices = set()
            if item != '':
                if '-' not in item:
                    # single device
                    fcp_addr = int(item, 16)
                    devices.add("%04x" % fcp_addr)
                else:
                    # a range of address
                    (_min, _max) = item.split('-')
                    _min = int(_min, 16)
                    _max = int(_max, 16)
                    for fcp_addr in range(_min, _max + 1):
                        devices.add("%04x" % fcp_addr)
                if fcp_devices.get(path_no):
                    fcp_devices[path_no].update(devices)
                else:
                    fcp_devices[path_no] = devices
        path_no = path_no + 1
    return fcp_devices


def shrink_fcp_list(fcp_list):
    """ Transform a FCP list to a string.

        :param fcp_list: (list) a list object contains FCPs.
        Case 1: only one FCP in the list.
            e.g. fcp_list = ['1A01']
        Case 2: all the FCPs are continuous.
            e.g. fcp_list =['1A01', '1A02', '1A03']
        Case 3: not all the FCPs are continuous.
            e.g. fcp_list = ['1A01', '1A02', '1A03',
                            '1A05',
                            '1AFF', '1B00', '1B01',
                            '1B04']
        Case 4: an empty list.
            e.g. fcp_list = []

        :return fcp_str: (str)
        Case 1: fcp_str = '1A01'
        Case 2: fcp_str = '1A01 - 1A03'
        Case 3: fcp_str = '1A01 - 1A03, 1A05,
                           1AFF - 1B01, 1B04'
        Case 4: fcp_str = ''
    """

    def __transform_fcp_list_into_str(local_fcp_list):
        """ Transform the FCP list into a string
            by recursively do the transformation
            against the first continuous range of the list,
            which is being shortened by list.pop(0) on the fly

            :param local_fcp_list:
            (list) a list object contains FCPs.

            In Python, hex is stored in the form of strings.
            Because incrementing is done on integers,
            we need to convert hex to an integer for doing math.
        """
        # Case 1: only one FCP in the list.
        if len(local_fcp_list) == 1:
            fcp_section.append(local_fcp_list[0])
        else:
            start_fcp = int(local_fcp_list[0], 16)
            end_fcp = int(local_fcp_list[-1], 16)
            count = len(local_fcp_list) - 1
            # Case 2: all the FCPs are continuous.
            if start_fcp + count == end_fcp:
                # e.g. hex(int('1A01',16)) is '0x1a01'
                section_str = '{} - {}'.format(
                    hex(start_fcp)[2:], hex(end_fcp)[2:])
                fcp_section.append(section_str)
            # Case 3: not all the FCPs are continuous.
            else:
                start_fcp = int(local_fcp_list.pop(0), 16)
                for idx, fcp in enumerate(local_fcp_list.copy()):
                    next_fcp = int(fcp, 16)
                    # pop the fcp if it is continuous with the last
                    # e.g.
                    # when start_fcp is '1A01',
                    # pop '1A02' and '1A03'
                    if start_fcp + idx + 1 == next_fcp:
                        local_fcp_list.pop(0)
                        continue
                    # e.g.
                    # when start_fcp is '1A01',
                    # next_fcp '1A05' is NOT continuous with the last
                    else:
                        end_fcp = start_fcp + idx
                        # e.g.
                        # when start_fcp is '1A01',
                        # end_fcp is '1A03'
                        if start_fcp != end_fcp:
                            # e.g. hex(int('1A01',16)) is '0x1a01'
                            section_str = '{} - {}'.format(
                                hex(start_fcp)[2:], hex(end_fcp)[2:])
                        # e.g.
                        # when start_fcp is '1A05',
                        # end_fcp is '1A05'
                        else:
                            section_str = hex(start_fcp)[2:]
                        fcp_section.append(section_str)
                        break
                # recursively transform if FCP list still not empty
                if local_fcp_list:
                    __transform_fcp_list_into_str(local_fcp_list)

    fcp_section = list()
    fcp_str = ''
    if fcp_list:
        # sort fcp_list in hex order, e.g.
        # before sort: ['1E01', '1A02', '1D03']
        # after sort:  ['1A02', '1D03', '1E01']
        fcp_list.sort()
        __transform_fcp_list_into_str(fcp_list)
        # return a string contains all FCP
        fcp_str = ', '.join(fcp_section).upper()
    return fcp_str


def verify_fcp_list_in_hex_format(fcp_list):
    """Verify each FCP in the list is in Hex format
    :param fcp_list: (list) a list object contains FCPs.
    """
    if not isinstance(fcp_list, list):
        errmsg = ('fcp_list ({}) is not a list object.'
                  '').format(fcp_list)
        raise exception.SDKInvalidInputFormat(msg=errmsg)
    # Verify each FCP should be a 4-digit hex
    for fcp in fcp_list:
        if not (len(fcp) == 4 and
                all(char in string.hexdigits for char in fcp)):
            errmsg = ('FCP list {} contains non-hex value.'
                      '').format(fcp_list)
            raise exception.SDKInvalidInputFormat(msg=errmsg)
