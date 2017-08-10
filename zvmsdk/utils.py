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


import commands
import errno
import functools
import os
import pwd
import re
import shutil
import six
import sys
import time
import traceback
import types

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


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


def parse_image_name(os_image_name):
    profile = os_image_name.split('-')[3]
    image_name = profile.split('_')[0]
    xcat_image_id = profile.split('_', 1)[1]
    image_id = xcat_image_id.replace('_', '-')
    return image_name, image_id


def get_image_version(os_image_name):
    os_version = os_image_name.split('-')[0]
    return os_version


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
        raise exception.ZVMSDKInternalError(msg=errmsg)


def get_zhcp_node():
    """Return zhcp node."""
    return CONF.xcat.zhcp.partition('.')[0]


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
                raise exception.ZVMInvalidInput(msg=msg)

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
                raise exception.ZVMInvalidInput(msg=msg)

            if invalid_type:
                msg = ("Invalid input types: %(argtypes)s; "
                       "Expected types: %(types)s" %
                       {'argtypes': str(argtypes), 'types': str(types)})
                LOG.info(msg)
                raise exception.ZVMInvalidInput(msg=msg)

            valid_keys = validkeys.get('valid_keys')
            if valid_keys:
                for k in kwargs.keys():
                    if k not in valid_keys:
                        msg = ("Invalid keyword: %(key)s; "
                               "Expected keywords are: %(keys)s" %
                               {'key': k, 'keys': str(valid_keys)})
                        LOG.info(msg)
                        raise exception.ZVMInvalidInput(msg=msg)
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


def get_xcatclient():
    return import_object('zvmsdk.xcatclient.XCATClient')


def xdsh(*args, **kwargs):
    return get_xcatclient().xdsh(*args, **kwargs)


def punch_xcat_auth_file(*args, **kwargs):
    return get_xcatclient().punch_xcat_auth_file(*args, **kwargs)


def get_xcat_version(*args, **kwargs):
    return get_xcatclient().get_xcat_version(*args, **kwargs)


def create_xcat_mgt_network(*args, **kwargs):
    return get_xcatclient().create_xcat_mgt_network(*args, **kwargs)


def get_xcat_url(*args, **kwargs):
    return get_xcatclient().get_xcat_url(*args, **kwargs)
