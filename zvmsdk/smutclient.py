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

from smutLayer import smut

from zvmsdk import client
from zvmsdk import config
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
def expect_invalid_smut_resp_data(data=''):
    """Catch exceptions when converting SMUT response data."""
    try:
        yield
    except (ValueError, TypeError, IndexError, AttributeError,
            KeyError) as err:
        LOG.error('Parse SMUT response data %s encounter error', data)
        raise exception.ZVMInvalidSMUTResponseDataError(msg=err)


class SMUTClient(client.ZVMClient):

    def __init__(self):
        self._smut = smut.SMUT()

    def _request(self, requestData):
        try:
            results = self._smut.request(requestData)
        except (ValueError, TypeError, IndexError, AttributeError,
            KeyError) as err:
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
        with expect_invalid_smut_resp_data():
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
