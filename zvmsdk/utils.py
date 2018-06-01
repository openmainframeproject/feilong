# Copyright 2017,2018 IBM Corp.
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

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


def execute(cmd):
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
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        rc = err.returncode
        output = err.output
    except Exception as err:
        err_msg = ('Command "%s" Error: %s' % (' '.join(cmd), str(err)))
        raise exception.SDKInternalError(msg=err_msg)

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
        zvmsdk_file_repo = os.path.join(CONF.file.sdk_file_repository,
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
        return text.encode('utf-8')
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
        msg = ('Invalid smut response data: %s. Error: %s' %
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
            msg = ('Invalid smut response data. Error: %s' %
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
def log_and_reraise_smut_request_failed(action=None):
    """Catch SDK base exception and print error log before reraise exception.

    msg: the error message to be logged.
    """
    try:
        yield
    except exception.SDKSMUTRequestFailed as err:
        msg = ''
        if action is not None:
            msg = "Failed to %s. " % action
        msg += "SMUT error: %s" % err.format_message()
        LOG.error(msg)
        raise exception.SDKSMUTRequestFailed(err.results, msg)


@contextlib.contextmanager
def ignore_errors():
    """Only execute the clauses and ignore the results"""
    try:
        yield
    except Exception as err:
        msg = 'ignore an error:%s' % err.format_message()
        LOG.debug(msg)
        pass


def get_smut_userid():
    """Get the userid of smut server"""
    cmd = ["sudo", "/sbin/vmcp", "query userid"]
    try:
        userid = subprocess.check_output(cmd,
                                         close_fds=True,
                                         stderr=subprocess.STDOUT).split()[0]
        return userid
    except Exception as err:
        msg = ("Could not find the userid of the smut server: %s") % err
        raise exception.SDKInternalError(msg=msg)


def get_namelist():
    """Generate namelist.

    Either through set CONF.zvm.namelist, or by generate based on smut userid.
    """
    if CONF.zvm.namelist is not None:
        # namelist length limit should be 64, but there's bug limit to 8
        # will change the limit to 8 once the bug fixed
        if len(CONF.zvm.namelist) <= 8:
            return CONF.zvm.namelist

    return ''.join(('NL', get_smut_userid().rjust(6, '0')[-6:]))


def generate_iucv_authfile(fn, client):
    """Generate the iucv_authorized_userid file"""
    lines = ['#!/bin/bash\n',
             'echo -n %s > /etc/iucv_authorized_userid\n' % client]
    with open(fn, 'w') as f:
        f.writelines(lines)


@wrap_invalid_resp_data_error
def translate_response_to_dict(rawdata, dirt):
    """Translate SMUT response to a python dictionary.

    SMUT response example:
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
        msg = ("Invalid smut response data. Error: No value matched with "
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

    header = bytes(' '.join((header, 'HLen: 0055', 'GZIP: 0')))
    with open(image_path, 'wb') as f:
        f.write(header)


@contextlib.contextmanager
def acquire_lock(lock):
    """ lock wrapper """
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def check_userid_exist(userid):
    cmd = 'sudo vmcp q %s' % userid
    rc, output = execute(cmd)
    if re.search('(^HCP\w\w\w003E)', output):
        # userid not exist
        return False
    return True
