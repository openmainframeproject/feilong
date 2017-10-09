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


import config
import log
import six
from zvmsdk import returncode


CONF = config.CONF
LOG = log.LOG


class SDKBaseException(Exception):
    """
    Inherit from this class and define a 'msg_fmt' property.
    That msg_fmt will get printf'd with the keyword arguments
    provided to the constructor.
    """
    msg_fmt = "z/VM SDK error: %(msg)s"
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, results=None, **kwargs):
        self.results = results
        self.kw = kwargs
        if 'code' in self.kw:
            try:
                self.kw['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs
            except Exception:
                LOG.exception('Exception in string format operation')
                for name, value in six.iteritems(kwargs):
                    LOG.error("%s: %s" % (name, value))

                message = self.msg_fmt

        self.message = message
        super(SDKBaseException, self).__init__(message)

    def format_message(self):
        return self.args[0]


class ZVMException(SDKBaseException):
    msg_fmt = 'ZVMException happened: %(msg)s'


class ZVMNetworkError(SDKBaseException):
    msg_fmt = "z/VM network error: %(msg)s"


class ZVMVirtualMachineNotExist(SDKBaseException):
    msg_fmt = 'Virtual machine %(userid)s does not exist in %(zvm_host)s'


class NotFound(SDKBaseException):
    msg_fmt = 'The resource can not be found'


class InvalidName(SDKBaseException):
    msg_fmt = 'Invalid name provided, reason is %(reason)s'


class ValidationError(SDKBaseException):
    safe = True
    code = 400
    msg_fmt = 'Validation error: %(detail)s'


class ZVMUnauthorized(SDKBaseException):
    code = 401


class SDKDatabaseException(SDKBaseException):
    msg_fmt = "SDK database error: %(msg)s"


class SDKInvalidInputNumber(SDKBaseException):
    def __init__(self, api, expected, provided):
        rc = returncode.errors['input']
        results = rc[0]
        results['modID'] = returncode.ModRCs['zvmsdk']
        results['rs'] = 1
        errormsg = rc[1][1] % {'api': api, 'expected': expected,
                               'provided': provided}
        super(SDKInvalidInputNumber, self).__init__(results=results,
                                                    message=errormsg)


class SDKInvalidInputTypes(SDKBaseException):
    def __init__(self, api, expected, inputtypes):
        rc = returncode.errors['input']
        results = rc[0]
        results['modID'] = returncode.ModRCs['zvmsdk']
        results['rs'] = 2
        errormsg = rc[1][2] % {'api': api, 'expected': expected,
                               'inputtypes': inputtypes}
        super(SDKInvalidInputTypes, self).__init__(results=results,
                                                   message=errormsg)


class SDKInvalidInputFormat(SDKBaseException):
    def __init__(self, msg):
        rc = returncode.errors['input']
        results = rc[0]
        results['modID'] = returncode.ModRCs['zvmsdk']
        results['rs'] = 3
        errormsg = rc[1][3] % {'msg': msg}
        super(SDKInvalidInputFormat, self).__init__(results=results,
                                                    message=errormsg)


class SDKInternalError(SDKBaseException):
    def __init__(self, msg, modID='zvmsdk', results=None):
        # if results is set, it means the internal error comes from
        # smut module, we need to keep the rc/rs value from SMUT
        rc = returncode.errors['internal']
        errormsg = rc[1][1] % {'msg': msg}
        if results is None:
            results = rc[0]
            results['rs'] = 1
            results['modID'] = returncode.ModRCs[modID]
        else:
            # SMUT internal error
            # Reset the overallRC in results to the overallRC value
            # corresponding to internal error
            results['overallRC'] = (rc[0]['overallRC'])
            results['modID'] = returncode.ModRCs['smut']
        super(SDKInternalError, self).__init__(results=results,
                                               message=errormsg)


class SDKObjectNotExistError(SDKBaseException):
    def __init__(self, obj_desc, modID='zvmsdk'):
        rc = returncode.errors['notExist']
        results = rc[0]
        results['modID'] = returncode.ModRCs[modID]
        results['rs'] = 1
        errormsg = rc[1][1] % {'obj_desc': obj_desc}
        super(SDKObjectNotExistError, self).__init__(results=results,
                                                     message=errormsg)


class SDKSMUTRequestFailed(SDKBaseException):

    def __init__(self, results, msg):
        results['modID'] = returncode.ModRCs['smut']
        super(SDKSMUTRequestFailed, self).__init__(results=results,
                                                   message=msg)


class SDKGuestOperationError(SDKBaseException):
    def __init__(self, rs, **kwargs):
        # kwargs can be used to contain different keyword for constructing
        # the rs error msg
        rc = returncode.errors['guest']
        results = rc[0]
        results['rs'] = rs
        errormsg = rc[1][rs] % kwargs
        super(SDKGuestOperationError, self).__init__(results=results,
                                                     message=errormsg)


class SDKNetworkOperationError(SDKBaseException):
    def __init__(self, rs, **kwargs):
        # kwargs can be used to contain different keyword for constructing
        # the rs error msg
        rc = returncode.errors['network']
        results = rc[0]
        results['rs'] = rs
        errormsg = rc[1][rs] % kwargs
        super(SDKNetworkOperationError, self).__init__(results=results,
                                                       message=errormsg)


class SDKImageOperationError(SDKBaseException):
    def __init__(self, rs, **kwargs):
        # kwargs can be used to contain different keyword for constructing
        # the rs error msg
        rc = returncode.errors['image']
        results = rc[0]
        results['rs'] = rs
        errormsg = rc[1][rs] % kwargs
        results['strError'] = errormsg
        super(SDKImageOperationError, self).__init__(results=results,
                                                     message=errormsg)


class SDKVolumeOperationError(SDKBaseException):
    def __init__(self, rs, **kwargs):
        # kwargs can be used to contain different keyword for constructing
        # the rs error msg
        rc = returncode.errors['volume']
        results = rc[0]
        results['rs'] = rs
        errormsg = rc[1][rs] % kwargs
        results['strError'] = errormsg
        super(SDKVolumeOperationError, self).__init__(results=results,
                                                      message=errormsg)
