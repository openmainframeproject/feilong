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
import functools
import os
import subprocess
import tempfile

from smutLayer import smut

from zvmsdk import client
from zvmsdk import config
from zvmsdk import constants as const
from zvmsdk import exception
from zvmsdk import log


CONF = config.CONF
LOG = log.LOG


def wrap_invalid_smut_resp_data_error(function):
    """Catch exceptions when using smut result data."""

    @functools.wraps(function)
    def decorated_function(*arg, **kwargs):
        try:
            return function(*arg, **kwargs)
        except (ValueError, TypeError, IndexError, AttributeError,
                KeyError) as err:
            raise exception.ZVMInvalidSMUTResponseDataError(msg=err)

    return decorated_function


@contextlib.contextmanager
def expect_invalid_smut_resp_data(results):
    """Catch exceptions when converting SMUT response data."""
    try:
        yield
    except (ValueError, TypeError, IndexError, AttributeError,
            KeyError) as err:
        results.pop('logEntries')
        LOG.error('Parse SMUT response data encounter error, results: %s',
                  results)
        raise exception.ZVMInvalidSMUTResponseDataError(msg=err)


@contextlib.contextmanager
def expect_smut_request_failed_and_reraise(exc, **kwargs):
    """Catch all kinds of smut request failure and reraise.

    exc: the exception that would be raised.
    """
    try:
        yield
    except exception.ZVMSMUTRequestFailed as err:
        msg = err.format_message()
        kwargs['msg'] = msg
        LOG.error('SMUT request failed: %s', msg)
        raise exc(results=err.results, **kwargs)
    except (exception.ZVMInvalidSMUTResponseDataError,
            exception.ZVMInternalError) as err:
        msg = err.format_message()
        kwargs['msg'] = msg
        LOG.error('SMUT request failed: %s', msg)
        raise exc(**kwargs)


class SMUTClient(client.ZVMClient):

    def __init__(self):
        self._smut = smut.SMUT()

    def _request(self, requestData):
        try:
            results = self._smut.request(requestData)
        except Exception as err:
            LOG.error('SMUT internal parse encounter error')
            raise exception.ZVMSMUTInternalError(msg=err)

        if results['overallRC'] != 0:
            raise exception.ZVMSMUTRequestFailed(results=results)
        return results

    def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Query power stat of %s' % userid)
        requestData = "PowerVM " + userid + " status"
        results = self._request(requestData)
        with expect_invalid_smut_resp_data(results):
            status = results['response'][0].partition(': ')[2]
        return status

    def guest_start(self, userid):
        """"Power on VM."""
        requestData = "PowerVM " + userid + " on"
        self._request(requestData)

    def guest_stop(self, userid):
        """"Power off VM."""
        requestData = "PowerVM " + userid + " off"
        self._request(requestData)

    def create_vm(self, userid, cpu, memory, disk_list, profile):
        """ Create VM and add disks if specified. """
        rd = ('makevm %(uid)s directory LBYONLY %(mem)im %(pri)s '
              '--cpus %(cpu)i --profile %(prof)s' %
              {'uid': userid, 'mem': memory,
               'pri': const.ZVM_USER_DEFAULT_PRIVILEGE,
               'cpu': cpu, 'prof': profile})

        if CONF.zvm.logonby_users:
            rd += (' --logonby "%s"' % CONF.zvm.logonby_users)

        if disk_list and 'is_boot_disk' in disk_list[0]:
            ipl_disk = CONF.zvm.user_root_vdev
            rd += (' --ipl %s' % ipl_disk)

        self._request(rd)

        if disk_list:
            # Add disks for vm
            self.add_mdisks(userid, disk_list)

    def _add_mdisk(self, userid, disk, vdev):
        """Create one disk for userid

        NOTE: No read, write and multi password specified, and
        access mode default as 'MR'.

        """
        size = disk['size']
        fmt = disk.get('format')
        disk_pool = disk.get('disk_pool') or CONF.zvm.disk_pool
        [diskpool_type, diskpool_name] = disk_pool.split(':')

        if (diskpool_type.upper() == 'ECKD'):
            action = 'add3390'
        else:
            action = 'add9336'

        rd = ' '.join(['changevm', userid, action, diskpool_name,
                       vdev, size, '--mode MR'])
        if fmt:
            rd += (' --filesystem %s' % fmt)

        self._request(rd)

    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None):
        """ Deploy image and punch config driver to target """
        # Get image location (TODO: update this image location)
        image_file = "/var/lib/zvmsdk/images/" + image_name
        # Unpack image file to root disk
        vdev = vdev or CONF.zvm.user_root_vdev
        cmd = ['/opt/zthin/bin/unpackdiskimage', userid, vdev, image_file]
        try:
            resp = subprocess.check_output(cmd, close_fds=True,
                                           stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            returncode = resp.returncode
            output = resp.output.split('\n')
            err_msg = ("unpackdiskimage failed with return code: %d."
                       % returncode)
            for line in output:
                if line.__contains__("ERROR:"):
                    err_msg.append('\n' + line)
            raise exception.ZVMGuestDeployFailed(userid=userid, msg=err_msg)
        except Exception as err:
            err_msg = ("unpackdiskimage failed: %s" % str(err))
            raise exception.ZVMGuestDeployFailed(userid=userid, msg=err_msg)

        # Purge guest reader
        rd = ("changevm %s purgerdr" % userid)
        with expect_smut_request_failed_and_reraise(
            exception.ZVMGuestDeployFailed, userid=userid):
            self._smut._request(rd)

        # Copy transport file to local
        if transportfiles:
            try:
                local_trans = tempfile.mktemp()
                if remotehost:
                    cmd = ("/usr/bin/scp -B %(remote)s:%(trans)s %(local)s" %
                           {'remote': remotehost, 'trans': transportfiles,
                            'local': local_trans})
                else:
                    cmd = ("/bin/cp %s %s" % (transportfiles, local_trans))
                resp = subprocess.check_output(cmd, close_fds=True,
                                               stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                err_msg = ("copy config drive to local failed: rc=%d" %
                           resp.returncode)
                raise exception.ZVMGuestDeployFailed(userid=userid,
                                                     msg=err_msg)
            except Exception as err:
                err_msg = ("copy config drive to local failed: %s" % str(err))
                raise exception.ZVMGuestDeployFailed(userid=userid,
                                                     msg=err_msg)

            # Punch config drive to guest userid
            rd = ("changevm %(uid)s punchfile %(file)s" %
                  {'uid': userid, 'file': local_trans})
            with expect_smut_request_failed_and_reraise(
                exception.ZVMGuestDeployFailed, userid=userid):
                self._smut._request(rd)
            # remove the local temp config drive
            if os.path.exists(local_trans):
                os.remove(local_trans)
