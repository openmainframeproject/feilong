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


class ZVMInvalidInput(SDKBaseException):
    msg_fmt = 'Input parameters is invalid: %(msg)s'


class ZVMVolumeError(SDKBaseException):
    msg_fmt = 'Volume error: %(msg)s'


class ZVMImageError(SDKBaseException):
    msg_fmt = "Image error: %(msg)s"


class ZVMGetImageFromXCATFailed(SDKBaseException):
    msg_fmt = 'Get image from xCAT failed: %(msg)s'


class ZVMNetworkError(SDKBaseException):
    msg_fmt = "z/VM network error: %(msg)s"


class ZVMXCATXdshFailed(SDKBaseException):
    msg_fmt = 'Execute xCAT xdsh command failed: %(msg)s'


class ZVMXCATCreateNodeFailed(SDKBaseException):
    msg_fmt = 'Create xCAT node %(node)s failed: %(msg)s'


class ZVMXCATCreateUserIdFailed(SDKBaseException):
    msg_fmt = 'Create xCAT user id %(userid)s failed: %(msg)s'


class ZVMXCATUpdateNodeFailed(SDKBaseException):
    msg_fmt = 'Update node %(node)s info failed: %(msg)s'


class ZVMGuestDeployFailed(SDKBaseException):
    msg_fmt = 'Deploy image on guest %(userid)s failed: %(msg)s'


class ZVMConfigDriveError(SDKBaseException):
    msg_fmt = 'Create configure drive failed: %(msg)s'


class ZVMRetryException(SDKBaseException):
    msg_fmt = 'retry connect to instance timeout: %(msg)s'


class ZVMVirtualMachineNotExist(SDKBaseException):
    msg_fmt = 'Virtual machine %(userid)s does not exist in %(zvm_host)s'


class ZVMDeleteVMFailed(SDKBaseException):
    msg_fmt = 'Delete vm %(userid)s failed: %(msg)s'


class NotFound(SDKBaseException):
    msg_fmt = 'The resource can not be found'


class zVMInvalidDataError(SDKBaseException):
    msg_fmt = 'Invalid data error: %(msg)s'


class InvalidName(SDKBaseException):
    msg_fmt = 'Invalid name provided, reason is %(reason)s'


class ValidationError(SDKBaseException):
    safe = True
    code = 400
    msg_fmt = 'Validation error: %(detail)s'


class zVMConfigException(SDKBaseException):
    msg_fmt = 'zVMConfig Error: %(msg)s'


class ZVMSMUTAuthorizeIUCVClientFailed(SDKBaseException):
    msg_fmt = 'Failed to authorized the iucv client %(client)s on vm %(vm)s '\
        'with reason: %(msg)s'


class ZVMInvalidResponseDataError(SDKBaseException):
    msg_fmt = 'Invalid data returned from zvm client: %(msg)s'


class ZVMUnauthorized(SDKBaseException):
    code = 401


class SDKUnsupportedImageBackend(SDKBaseException):
    msg_fmt = 'Unsupported SDK image backend %(msg)s'


class SDKImageImportException(SDKBaseException):
    msg_fmt = 'Error detected during image import: %s(msg)s'


class DatabaseException(SDKBaseException):
    msg_fmt = "SDK database error: %(msg)s"


class DBTimeout(DatabaseException):
    msg_fmt = "SDK database operation timeout: %(msg)s"


class ZVMInvalidInputNumber(SDKBaseException):
    def __init__(self, api, expected, provided):
        rc = returncode.errors['input']
        results = rc[0]
        results['modID'] = returncode.ModRCs['zvmsdk']
        results['rs'] = 1
        errormsg = rc[1][1] % {'api': api, 'expected': expected,
                               'provided': provided}
        results['strError'] = errormsg
        super(ZVMInvalidInputNumber, self).__init__(results=results,
                                                    message=errormsg)


class ZVMInvalidInputtypes(SDKBaseException):
    def __init__(self, api, expected, inputtypes):
        rc = returncode.errors['input']
        results = rc[0]
        results['modID'] = returncode.ModRCs['zvmsdk']
        results['rs'] = 2
        errormsg = rc[1][2] % {'api': api, 'expected': expected,
                               'inputtypes': inputtypes}
        results['strError'] = errormsg
        super(ZVMInvalidInputtypes, self).__init__(results=results,
                                                   message=errormsg)


class ZVMInvalidInputFormat(SDKBaseException):
    def __init__(self, msg):
        rc = returncode.errors['input']
        results = rc[0]
        results['modID'] = returncode.ModRCs['zvmsdk']
        results['rs'] = 3
        errormsg = rc[1][3] % {'msg': msg}
        results['strError'] = errormsg
        super(ZVMInvalidInputFormat, self).__init__(results=results,
                                                    message=errormsg)


class ZVMSDKInternalError(SDKBaseException):
    def __init__(self, msg, modID='zvmsdk'):
        rc = returncode.errors['internal']
        results = rc[0]
        results['rs'] = 1
        errormsg = rc[1][1] % {'msg': msg}
        results['strError'] = errormsg
        results['modID'] = returncode.ModRCs[modID]
        super(ZVMSDKInternalError, self).__init__(results=results,
                                                  message=errormsg)


class ZVMClientInternalError(ZVMSDKInternalError):
    def __init__(self, msg):
        super(ZVMClientInternalError, self).__init__(msg=msg,
                                                     modID = 'zvmsdk')


class ZVMObjectNotExistError(SDKBaseException):
    def __init__(self, object, modID='zvmsdk'):
        rc = returncode.errors['notExist']
        results = rc[0]
        results['modID'] = returncode.ModRCs[modID]
        results['rs'] = 1
        errormsg = rc[1][1] % {'object': object}
        results['strError'] = errormsg
        super(ZVMObjectNotExistError, self).__init__(results=results,
                                                     message=errormsg)


class ZVMClientRequestFailed(SDKBaseException):

    def __init__(self, rd=None, results=None, msg=''):
        self.msg_fmt = 'zVM client request failed: %(msg)s'
        # When the backend is smut, results should be passed in.
        if results:
            results.pop('logEntries')
            results['modID'] = returncode.ModRCs['smut']
            if rd is not None:
                msg += ("RequestData: '%s'" % rd)
            msg += ("Results: %s" % str(results))
            super(ZVMClientRequestFailed, self).__init__(results=results,
                                                         msg=msg)
        else:
            super(ZVMClientRequestFailed, self).__init__(msg=msg)


class SDKGuestOperationError(SDKBaseException):
    def __init__(self, rs, **kwargs):
        # kwargs can be used to contain different keyword for constructing
        # the rs error msg
        rc = returncode.errors['guest']
        results = rc[0]
        results['rs'] = rs
        errormsg = rc[1][rs] % kwargs
        results['strError'] = errormsg
        super(SDKGuestOperationError, self).__init__(results=results,
                                                     message=errormsg)
